# UDOS Runtime OBJ Modules

This directory contains target-side text `OBJ1` runtime modules that UDOS
`ALINK.PRG` can parse from `LIB/`.

The sibling `src/runtime/modules/` directory is the host/reference JSON-style object
format used by the Python linker. Keep the two formats separate until the host
and UDOS object readers converge.

Current status:

- `rt_i_to_f.obj` converts an unsigned 16-bit integer in `A` low and `X` high
  to a little-endian IEEE-754 binary32 value through the destination pointer in
  zero page `$02/$03`.
- `rt_s_to_f.obj` converts a signed 16-bit integer in `A` low and `X` high to a
  little-endian IEEE-754 binary32 value through the destination pointer in zero
  page `$02/$03`.
- `rt_f_to_i.obj` converts a little-endian IEEE-754 binary32 value read through
  the source pointer in zero page `$02/$03` back to a signed 16-bit integer in
  `A` low and `X` high, truncating toward zero. Unsupported and out-of-range
  inputs return zero.
- `rt_f_add.obj` adds two non-negative REAL32 values with sums below `128.0`.
  It reads source pointers from zero page `$02/$03` and `$04/$05`, writes
  through the destination pointer in `$06/$07`, accumulates in Q8.8 precision,
  and imports `rt_s_to_f` so ALINK must resolve its transitive runtime helper
  dependency.
- `rt_f_sub.obj` subtracts two non-negative REAL32 values where the result is
  greater than or equal to zero and below `128.0`. It reads source pointers from
  zero page `$02/$03` and `$04/$05`, writes through the destination pointer in
  `$06/$07`, accumulates in Q8.8 precision, returns zero on underflow, and
  imports `rt_s_to_f` so ALINK must resolve its transitive runtime helper
  dependency.
- `rt_f_mul.obj` multiplies two non-negative REAL32 values where the Q8.8
  product is below `128.0`. It reads source pointers from zero page `$02/$03`
  and `$04/$05`, writes through the destination pointer in `$06/$07`, returns
  zero on overflow, and imports `rt_s_to_f` so ALINK must resolve its
  transitive runtime helper dependency.
- `rt_f_div.obj` divides two non-negative REAL32 values where the Q8.8 quotient
  is below `128.0`. It reads source pointers from zero page `$02/$03` and
  `$04/$05`, writes through the destination pointer in `$06/$07`, returns zero
  on divide-by-zero or wider results, and imports `rt_s_to_f` so ALINK must
  resolve its transitive runtime helper dependency.
- `rt_f_cmp.obj` compares two non-negative REAL32 values below `128.0`. It
  reads source pointers from zero page `$02/$03` and `$04/$05`, converts both
  operands through Q8.8 fixed-point precision, and returns signed byte
  comparison in `A`/`X` (`-1`, `0`, or `1`).
- `rt_f_abs.obj` copies a REAL32 value read through zero page `$02/$03` to the
  destination pointer in `$06/$07`, clearing the sign bit in the copied value.
- `rt_f_sqrt.obj` reads a REAL32 value through zero page `$02/$03`, writes the
  result through `$06/$07`, and currently returns floor square roots for
  non-negative unsigned 16-bit REAL integer inputs. Unsupported inputs write zero.
- `rt_print_f.obj` prints non-negative REAL32 values below `128.0` read through
  zero page `$02/$03` as decimal text through the C64 `CHROUT` vector. It
  converts through Q8.8 fixed-point precision and emits up to two fractional
  decimal digits with trailing zeroes trimmed.
- ALINK's current direct-PRG REAL proof cases lower the reachable ACTC body
  operations into target-side calls to the referenced REAL helper OBJ modules,
  including transitive helper imports such as `rt_s_to_f`.
- `rt_gfx_bgcolor.obj` sets the VIC-II background color register `$D021`. It
  expects the color in `A`, masks it to the low nybble, stores it, and returns
  with `RTS`.
- `rt_gfx_bordercolor.obj` sets the VIC-II border color register `$D020`. It
  expects the color in `A`, masks it to the low nybble, stores it, and returns
  with `RTS`.
- `rt_gfx_vic_bank.obj` selects the VIC-II 16 KB memory bank through CIA2
  register `$DD00`. It expects logical bank `0..3` in `A`, programs `$DD02`
  bits 0-1 as outputs, writes the C64's inverted bank bits to `$DD00` while
  preserving the upper six bits, and returns with `RTS`.
- `rt_gfx_screen_base.obj` sets the VIC-II screen-memory base bits in `$D018`.
  It expects a CARD address in `X`/`Y`, derives the 1 KB screen base from bits
  `$3C00`, preserves the low `$D018` bits, and returns with `RTS`.
- `rt_gfx_bitmap_base.obj` sets the VIC-II bitmap-memory base bit in `$D018`.
  It expects a CARD address in `X`/`Y`, uses address bit `$2000`, preserves the
  other `$D018` bits, and returns with `RTS`.
- `rt_gfx_screen_cell.obj` writes one character byte to the default C64 screen
  at `$0400 + y*40 + x`. It expects `x` in `A`, `y` in `X`, and the character
  byte in `Y`, then returns with `RTS`.
- `rt_gfx_color_cell.obj` writes one color nybble to C64 color RAM at
  `$D800 + y*40 + x`. It expects `x` in `A`, `y` in `X`, and color in `Y`,
  masks the color to the low nybble, and returns with `RTS`.
- `rt_gfx_screen_copy.obj` copies 1000 bytes from a source CARD address to the
  default C64 screen at `$0400-$07E7`. It expects the source address in `X`/`Y`
  and returns with `RTS`.
- `rt_gfx_color_copy.obj` copies 1000 low nybbles from a source CARD address to
  C64 color RAM at `$D800-$DBE7`. It expects the source address in `X`/`Y`,
  masks each source byte to `$0F`, and returns with `RTS`.
- `rt_gfx_bitmap_fill.obj` fills the default C64 bitmap memory range
  `$2000-$3F3F` with one byte. It expects the fill byte in `A` and returns with
  `RTS`.
- `rt_gfx_bitmap_copy.obj` copies 8000 bytes from a source CARD address to the
  default C64 bitmap memory range `$2000-$3F3F`. It expects the source address
  in `X`/`Y` and returns with `RTS`.
- `rt_gfx_bitmap_on.obj` enables standard VIC-II bitmap mode by setting bit 5 of
  `$D011`, preserving the other control bits, and returning with `RTS`.
- `rt_gfx_bitmap_off.obj` disables VIC-II bitmap mode by clearing bit 5 of
  `$D011`, preserving the other control bits, and returning with `RTS`.
- `rt_gfx_mbitmap_on.obj` enables VIC-II multicolor bitmap mode by setting bit 5
  of `$D011` and bit 4 of `$D016`, preserving the other control bits, and
  returning with `RTS`.
- `rt_gfx_mbitmap_off.obj` disables VIC-II multicolor bitmap mode by clearing
  bit 5 of `$D011` and bit 4 of `$D016`, preserving the other control bits, and
  returning with `RTS`.
- `rt_sid_freq.obj` sets a SID voice frequency word. It expects the voice index
  in `A`, frequency low byte in `X`, and frequency high byte in `Y`; it stores
  to `$D400+7*voice` and `$D401+7*voice`, then returns with `RTS`.
- `rt_sid_pulse.obj` sets a SID voice pulse-width word. It expects the voice
  index in `A`, pulse low byte in `X`, and pulse high byte in `Y`; it masks
  the high byte to the SID's 12-bit pulse-width range, stores to
  `$D402+7*voice` and `$D403+7*voice`, then returns with `RTS`.
- `rt_sid_state.obj` exports a three-byte SID control shadow used by the
  waveform and gate helpers. It is data, not a callable routine.
- `rt_sid_wave.obj` sets a SID voice waveform/control byte exactly. It expects
  the voice index in `A` and the waveform/control byte in `Y`; it updates
  `rt_sid_state[voice]`, stores to `$D404+7*voice`, then returns with `RTS`.
  Gate helpers use the shadow because SID control registers should not be
  treated as a reliable read/modify/write source.
- `rt_sid_on.obj` sets a SID voice gate bit while preserving the last
  `SidWave` control byte from `rt_sid_state`. It expects the voice index in
  `A`; it stores to `$D404+7*voice`, then returns with `RTS`.
- `rt_sid_off.obj` clears a SID voice gate bit while preserving the last
  `SidWave` control byte from `rt_sid_state`. It expects the voice index in
  `A`; it stores to `$D404+7*voice`, then returns with `RTS`.
- `rt_sid_rst.obj` clears the SID register block `$D400-$D418` and the linked
  `rt_sid_state`, `rt_sid_filter_state`, and `rt_sid_volume_state` shadows,
  then returns with `RTS`.
- `rt_sid_ad.obj` sets a SID voice attack/decay byte. It expects the voice
  index in `A` and the attack/decay byte in `Y`; it stores to
  `$D405+7*voice`, then returns with `RTS`.
- `rt_sid_sr.obj` sets a SID voice sustain/release byte. It expects the voice
  index in `A` and the sustain/release byte in `Y`; it stores to
  `$D406+7*voice`, then returns with `RTS`.
- `rt_sid_filter_state.obj` exports a one-byte shadow for SID filter routing
  and resonance register `$D417`. It is data, not a callable routine.
- `rt_sid_route.obj` sets the SID filter routing low nybble. It expects the
  route mask in `A`, preserves the resonance nybble from
  `rt_sid_filter_state`, stores to `$D417`, updates the shadow, and returns
  with `RTS`.
- `rt_sid_res.obj` sets the SID filter resonance high nybble. It expects the
  resonance value in `A`, preserves the routing nybble from
  `rt_sid_filter_state`, stores to `$D417`, updates the shadow, and returns
  with `RTS`.
- `rt_sid_cutoff.obj` sets the SID filter cutoff word. It expects the cutoff
  low byte in `X` and high byte in `Y`; it stores the low three cutoff bits to
  `$D415` and the upper eight cutoff bits to `$D416`, then returns with `RTS`.
- `rt_sid_volume_state.obj` exports a one-byte shadow for SID filter mode and
  volume register `$D418`. It is data, not a callable routine.
- `rt_sid_mode.obj` sets the SID filter mode high nybble. It expects the mode
  value in `A`, preserves the volume nybble from `rt_sid_volume_state`, stores
  to `$D418`, updates the shadow, and returns with `RTS`.
- `rt_sid_vol.obj` sets the SID master volume nybble. It expects the volume in
  `A`, preserves the filter mode nybble from `rt_sid_volume_state`, stores to
  `$D418`, updates the shadow, and returns with `RTS`.
- `rt_sid_osc3.obj` returns SID oscillator 3 readback register `$D41B` in `A`,
  then returns with `RTS`.
- `rt_sid_env3.obj` returns SID envelope 3 readback register `$D41C` in `A`,
  then returns with `RTS`.
- `rt_sprite_on.obj` is the first target-side SID/sprite helper implemented as
  machine code. It expects a sprite index in `A`, sets the matching enable bit
  in VIC-II register `$D015`, and returns with `RTS`; the ALINK direct-PRG
  probe proves the helper is selected from `LIB/` and carried in the final
  linked program.
- `rt_sprite_off.obj` is the matching machine-code helper for clearing a sprite
  enable bit. It expects a sprite index in `A`, clears the matching bit in
  `$D015`, and returns with `RTS`; the probe seeds `$D015` first so the target
  run verifies an actual bit-clear side effect.
- `rt_sprite_hit.obj` returns the sprite-sprite collision register `$D01E` in
  `A`, then returns with `RTS`.
- `rt_sprite_hit_bg.obj` returns the sprite-background collision register
  `$D01F` in `A`, then returns with `RTS`.
- `rt_sprite_color.obj` is the first per-sprite color helper. It expects the
  color nybble in `A` and the sprite index in `X`, stores to `$D027,X`, and
  returns with `RTS`; the probe verifies slot 2 writes through `$D029`.
- `rt_sprite_pos.obj` positions a sprite using the full VIC-II 9-bit X
  coordinate. It expects the sprite index in `A`, X low byte in `X`, Y in `Y`,
  and the X high bit in carry; it stores `$D000+2*slot`, `$D001+2*slot`, and
  sets or clears the sprite bit in `$D010`.
- `rt_sprite_data.obj` writes the sprite data pointer for the default screen
  block from a sprite data address. It expects the sprite index in `A`, the
  address low byte in `X`, and the address high byte in `Y`, computes
  `addr / 64`, stores the pointer byte to `$07F8+slot`, and returns with `RTS`.
- `rt_sprite_ptr.obj` writes the raw sprite pointer byte for the default screen
  block. It expects the pointer byte in `A` and sprite index in `X`, stores to
  `$07F8+slot`, and returns with `RTS`.
- `rt_sprite_mc.obj`, `rt_sprite_xexp.obj`, `rt_sprite_yexp.obj`, and
  `rt_sprite_prio.obj` are per-sprite bit-control helpers. They expect the
  sprite index in `A` and a boolean flag in `Y`, then set or clear the matching
  bit in `$D01C`, `$D01D`, `$D017`, or `$D01B` respectively.
- `rt_sprite_set_mc.obj` sets the shared multicolor sprite registers. It
  expects multicolor 0 in `A` and multicolor 1 in `X`, stores to `$D025` and
  `$D026`, and returns with `RTS`.
- `rt_joy.obj` reads a C64 joystick port selected by `A` (`1` for CIA1
  port B at `$DC01`, any other value for CIA1 port A at `$DC00`) and returns an
  active-high bitfield in `A`: bit 0 up, bit 1 down, bit 2 left, bit 3 right,
  bit 4 button 1/fire, and bit 5 button 2 using the project POT-line threshold
  convention.
- `rt_js.obj` exports two bytes of linked joystick presence state, one byte per
  control port.
- `rt_jp.obj` imports `rt_joy` and `rt_js`, latches a port's state to `1` after
  observed joystick activity, and returns the latched byte. This is
  observed/inferred presence; a passive idle C64 joystick cannot be electrically
  distinguished from no joystick by this helper.
- `rt_jb1.obj` and `rt_jb2.obj` import `rt_joy` and return `1` when joystick
  button 1 or button 2 is active on the selected port, otherwise `0`.
- `rt_ms.obj` exports seven bytes of linked helper state:
  initialized, last raw POT X, last raw POT Y, accumulated X, accumulated Y,
  buttons, and inferred presence.
- `rt_mp.obj` samples the selected control port, updates
  `rt_ms`, and returns inferred presence in `A`. It treats normal fire
  as mouse button 1 and a selected POT line below `$80` as mouse button 2. The
  first poll initializes the raw POT baseline before movement deltas are
  accumulated.
- `rt_mseen.obj` returns the last inferred mouse presence byte from `rt_ms`.
- `rt_mx.obj` returns the current 8-bit accumulated mouse X position from
  `rt_ms`.
- `rt_my.obj` returns the current 8-bit accumulated mouse Y position from
  `rt_ms`.
- `rt_mb.obj` returns the current mouse button bitfield from `rt_ms`: bit 0
  button 1, bit 1 button 2.
- `rt_mb1.obj` and `rt_mb2.obj` import `rt_mb` and return `1` when mouse
  button 1 or button 2 is active, otherwise `0`.
- `rt_dbf_state.obj` exports thirteen bytes of linked DBF state: active handle,
  total-record low/high bytes, current-record low/high bytes, DBF header-size
  low/high bytes, DBF record-size low/high bytes, original filename pointer
  low/high bytes, and staged file-length low/high bytes.
- `rt_dbf_open.obj` expects a CARD filename pointer in `X`/`Y`, stages up to a
  16-bit DBF file into the DBF REU slot, reads the DBF header, and returns
  handle `1` in `A` when the header can be parsed. It returns zero on missing
  file, missing REU, too-short input, larger staged files, or staging failure.
- `rt_dbf_create.obj` expects a CARD filename pointer in `X`/`Y`, clears the
  DBF state, stages a new zero-field DBF image with header length 12 and record
  length 1 in the DBF REU slot, remembers the filename pointer, and returns
  handle `1` in `A` after all header bytes are staged. Use `rt_dbf_save.obj` to
  persist the created image.
- `rt_dbf_close.obj` expects a DBF handle in `A` and clears the active handle
  when it matches the current DBF state.
- `rt_dbf_go.obj` expects a DBF handle in `A` and a one-based target record
  number in `Y`. It updates the current-record state and returns `1` in `A`
  when the handle is active and the target is in range; otherwise it returns
  zero and leaves the current-record state unchanged.
- `rt_dbf_fieldcount.obj` expects a DBF handle in `A` and returns the DBF field
  count derived from the staged header size, or zero when the handle is inactive
  or the staged header size is invalid.
- `rt_dbf_fieldlen.obj` expects a DBF handle in `A` and a one-based field index
  in `Y`. It returns the field length byte from the staged DBF field descriptor,
  or zero when the handle, field index, or staged header bounds are invalid.
- `rt_dbf_readbyte.obj` expects a DBF handle in `A` and a current-record byte
  offset in `Y`. It returns the raw byte from the staged DBF record, including
  offset zero for the delete flag, or zero when the handle is inactive, the
  current record is invalid, the offset is out of range, or the REU read fails.
- `rt_dbf_readfieldbyte.obj` expects a DBF handle in `A`, a one-based field
  index in `X`, and a zero-based field byte offset in `Y`. It imports
  `rt_dbf_fieldlen` and `rt_dbf_readbyte`, validates the requested field and
  offset, and returns zero on invalid inputs, offset overflow, or read failure.
- `rt_dbf_writefieldbyte.obj` expects a DBF handle in `A`, a one-based field
  index in `X`, a zero-based field byte offset in `Y`, and the byte value in
  zero page `$E0`. It imports `rt_dbf_fieldlen` and `rt_dbf_writebyte`,
  validates the requested field and offset, and returns `1` on success or zero
  on invalid inputs, offset overflow, or write failure.
- `rt_dbf_writebyte.obj` expects a DBF handle in `A`, a current-record byte
  offset in `X`, and the byte value in `Y`. It writes into the staged DBF
  record and returns `1` in `A` on success, or zero when the handle is inactive,
  the current record is invalid, the offset is out of range, or the REU write
  fails.
- `rt_dbf_append.obj` expects a DBF handle in `A`, appends one blank record to
  the staged DBF image, increments the staged record count, makes the appended
  record current, and returns `1` in `A` on success.
- `rt_dbf_pack.obj` expects a DBF handle in `A`, removes deleted records from
  the staged DBF image while preserving non-deleted records in order, updates
  the staged record count, sets the current record to one when records remain
  or zero when none remain, and returns `1` in `A` on success. The helper
  imports `rt_dbf_pack_step` and `rt_dbf_pack_write` so the lower-level staged
  REU byte operations stay link-selected with the pack feature.
- `rt_dbf_pack_read.obj`, `rt_dbf_pack_write.obj`, `rt_dbf_pack_copy.obj`, and
  `rt_dbf_pack_step.obj` are internal support modules for `rt_dbf_pack.obj`.
  They read, write, copy, and process one staged DBF record using UDOS REU
  byte-transfer services.
- `rt_dbf_save.obj` expects a DBF handle in `A`, streams the staged DBF image
  back to the filename remembered by `rt_dbf_open` or `rt_dbf_create`, and
  returns `1` in `A` after the write and close succeed.
- `rt_dbf_delete.obj` imports `rt_dbf_writebyte`, writes `*` to current-record
  offset zero, and returns `1` on success.
- `rt_dbf_undelete.obj` imports `rt_dbf_writebyte`, writes space to
  current-record offset zero, and returns `1` on success.
- `rt_dbf_deleted.obj` imports `rt_dbf_readbyte`, reads current-record offset
  zero, and returns `1` when the DBF delete flag is `*`, otherwise `0`.
- `rt_dbf_headerlen.obj` expects a DBF handle in `A` and returns the staged
  DBF header-size low byte in `A`, or zero when the handle is inactive.
- `rt_dbf_recordlen.obj` expects a DBF handle in `A` and returns the staged
  DBF record-size low byte in `A`, or zero when the handle is inactive.
- `rt_dbf_totalrecs.obj` expects a DBF handle in `A` and returns the current
  DBF header record-count low byte in `A`, or zero when the handle is inactive.
- `rt_dbf_currrecno.obj` expects a DBF handle in `A` and returns the current
  record number low byte in `A`, or zero when the handle is inactive. Open sets
  this to `1` when the header record count is nonzero.
