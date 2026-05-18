# UDOS Runtime OBJ Modules

This directory contains target-side text `OBJ1` runtime modules that UDOS
`ALINK.PRG` can parse from `LIB/`.

The sibling `src/runtime/modules/` directory is the host/reference JSON-style object
format used by the Python linker. Keep the two formats separate until the host
and UDOS object readers converge.

Current status:

- `rt_f_add.obj` is a partial REAL add helper. It preserves the current stack
  contract, implements exact zero identity for either side
  (`x + +0.0 = x`, `+0.0 + x = x`), handles same-sign equal-power-of-two sums
  by exponent increment, including `1.0 + 1.0 = 2.0`,
  `2.0 + 2.0 = 4.0`, `4.0 + 4.0 = 8.0`, and
  `-2.0 + -2.0 = -4.0`, and still handles exact `1.5 + 1.5 = 3.0`.
  It also handles adjacent-exponent power-of-two sums such as
  `2.0 + 1.0 = 3.0`, `1.0 + 2.0 = 3.0`, and
  `-2.0 + -1.0 = -3.0`, adjacent-exponent mixed-sign differences
  such as `2.0 + -1.0 = 1.0`, `1.0 + -2.0 = -1.0`,
  `-2.0 + 1.0 = -1.0`, and `-1.0 + 2.0 = 1.0`, gap-two
  power-of-two sums such as `4.0 + 1.0 = 5.0`, and gap-two mixed-sign
  differences such as `4.0 + -1.0 = 3.0`, `1.0 + -4.0 = -3.0`,
  `-4.0 + 1.0 = -3.0`, and `-1.0 + 4.0 = 3.0`. Equal-and-opposite
  cancellation is proven for the current direct `2.0 + -2.0` harness case,
  but broader mixed-sign addition remains incomplete. Other non-zero inputs still return REAL32 zero, so it is
  not the final IEEE-754 addition implementation.
- `rt_f_sub.obj` is a partial REAL subtract helper. It preserves the same stack
  contract, implements `x - +0.0 = x`, `+0.0 - x` by flipping the sign bit, and
  handles equal signed power-of-two subtraction as zero, including
  `2.0 - 2.0 = 0.0` and `-2.0 - -2.0 = 0.0`, plus exact
  `2.0 - 1.0 = 1.0`. It also handles adjacent-exponent power-of-two
  differences such as `4.0 - 2.0 = 2.0`, `2.0 - 4.0 = -2.0`, and
  `-4.0 - -2.0 = -2.0`, plus gap-two differences such as
  `4.0 - 1.0 = 3.0` and `1.0 - 4.0 = -3.0`, plus
  adjacent-exponent mixed-sign sums such as `2.0 - -1.0 = 3.0`,
  `1.0 - -2.0 = 3.0`, `-2.0 - 1.0 = -3.0`, and
  `-1.0 - 2.0 = -3.0`, and gap-two mixed-sign sums such as
  `4.0 - -1.0 = 5.0`, `1.0 - -4.0 = 5.0`,
  `-4.0 - 1.0 = -5.0`, and `-1.0 - 4.0 = -5.0`. Other non-zero pairs still return REAL32 zero,
  so it is not the final IEEE-754 subtraction
  implementation.
- `rt_f_mul.obj` is a partial REAL multiply helper. It preserves the same stack
  contract, implements zero identity, implements `x * 1.0 = x` and
  `1.0 * x = x`, and handles low-word-zero values scaled by an exact
  power-of-two operand using exponent addition plus sign-bit xor, including
  `2.0 * 2.0 = 4.0`, `4.0 * 2.0 = 8.0`,
  `-2.0 * 2.0 = -4.0`, `-2.0 * -2.0 = 4.0`,
  `1.5 * 2.0 = 3.0`, `2.0 * 1.5 = 3.0`, `-1.5 * 2.0 = -3.0`,
  `1.5 * -2.0 = -3.0`, `-1.5 * -2.0 = 3.0`, `1.5 * 1.5 = 2.25`, and
  `0.75 * 0.75 = 0.5625`. Other non-zero pairs still return REAL32 zero, so
  it is not the final IEEE-754 multiplication implementation.
- `rt_f_div.obj` is a partial REAL divide helper. It preserves the same stack
  contract, implements zero numerator and divide-by-zero as REAL32 zero,
  implements `x / 1.0 = x`, and handles low-word-zero numerators divided by
  an exact power-of-two denominator using exponent subtraction plus
  sign-bit xor, including `4.0 / 2.0 = 2.0`,
  `8.0 / 2.0 = 4.0`, `2.0 / 4.0 = 0.5`,
  `-4.0 / 2.0 = -2.0`, `2.0 / -4.0 = -0.5`,
  `3.0 / 2.0 = 1.5`, `1.5 / 2.0 = 0.75`, `-3.0 / 2.0 = -1.5`,
  `3.0 / -2.0 = -1.5`, `-3.0 / -2.0 = 1.5`, `1.5 / 1.5 = 1.0`, and
  `1.5 / 0.75 = 2.0`, `1.0 / 3.0 = 0.3333333432674407958984375`, and
  `1.0 / 10.0 = 0.100000001490116119384765625`. Other non-zero pairs still
  return REAL32 zero, so it is not the final IEEE-754 division
  implementation.
- `rt_i_to_f.obj` is the first target-side integer-to-REAL helper. It converts
  one non-negative 16-bit stack cell to exact REAL32, including values such as
  `1`, `7`, `255`, `256`, and `65535`. The current UDOS-native compiler uses
  it only for the narrow `BYTE`/`CARD` to REAL bridge. Signed `INT` conversion
  is still intentionally not routed through it, because the current helper
  treats the incoming cell as an unsigned magnitude.
- `rt_s_to_f.obj` is the first target-side signed-`INT` to REAL helper. It
  converts one 16-bit two's-complement stack cell to exact REAL32 by deriving a
  branchless sign mask, converting the resulting magnitude through
  `rt_i_to_f`, and then applying the REAL sign bit. The current UDOS-native
  compiler uses it only for the narrow `INT` variable-to-REAL bridge.
- `rt_print_f.obj` is the first target-side REAL print wrapper. It preserves
  the current stack contract and routes the current narrow `PrintR` / `PrintRE`
  lowering through the runtime-side REAL print intrinsic. The current proven
  UDOS-native slice is intentionally narrow but no longer limited to
  low-word-zero values: `REAL X`, `X=REAL(7)`, `PrintRE(X)`, fractional
  dyadic cases such as `A=REAL(3)`, `B=REAL(2)`, `X=A/B`, `PrintRE(X)`
  producing `1.5`, `X=X/B`, `PrintRE(X)` producing `0.75`,
  `A=REAL(1)`, `B=REAL(8)`, `X=A/B`, `PrintRE(X)` producing `0.125`,
  `A=REAL(1)`, `B=REAL(32)`, `X=A/B`, `PrintRE(X)` producing `0.03125`,
  `A=REAL(1)`, `B=REAL(64)`, `X=A/B`, `PrintRE(X)` producing `0.015625`,
  `A=REAL(1)`, `B=REAL(256)`, `X=A/B`, `PrintRE(X)` producing `0.00390625`,
  and `A=REAL(1)`, `B=REAL(32768)`, `X=A/B`, `PrintRE(X)` producing
  `0.000030517578125`,
  signed dyadic cases such as `INT N=[0]`, `N=0-1`, `A=REAL(N)`,
  `B=REAL(2)`, `X=A/B`, `PrintRE(X)` producing `-0.5`, and
  low-word-nonzero dyadic cases such as `A=REAL(129)`, `B=REAL(256)`,
  `X=A/B`, `PrintRE(X)` producing `0.50390625`, plus first end-to-end
  arithmetic print cases such as `X=X+A` after `X=1.5`, `A=1.5`,
  `PrintRE(X)` producing `3`, `X=A+B` with `A=4.0`, `B=-1.0`
  producing `3`, `X=A+B` with `A=1.0`, `B=-4.0` producing `-3`,
  `X=A+B` with `A=-1.0`, `B=4.0` producing `3`,
  `X=A-B` with `A=4.0`, `B=1.0` producing `3`,
  `X=A-B` with `A=4.0`, `B=-1.0` producing `5`,
  `X=A-B` with `A=-1.0`, `B=4.0` producing `-5`, and
  `X=A*B` with `A=1.5`, `B=2.0` producing `3`,
  `X=A*B` with `A=-1.5`, `B=2.0` producing `-3`,
  `X=A*B` with `A=1.5`, `B=-2.0` producing `-3`,
  `X=A*B` with `A=-1.5`, `B=-2.0` producing `3`,
  `X=A*B` with `A=1.5`, `B=1.5` producing `2.25`,
  `X=A*B` with `A=0.75`, `B=0.75` producing `0.5625`,
  `X=A/B` with `A=-3.0`, `B=2.0` producing `-1.5`,
  `X=A/B` with `A=3.0`, `B=-2.0` producing `-1.5`, and
  `X=A/B` with `A=-3.0`, `B=-2.0` producing `1.5`,
  and the linked helper-trailer model itself is now proven on a real
  `ALINK`-produced direct program: `A=REAL(1)`, `B=REAL(8)`, `X=A/B`,
  `PrintRE(X)` still produces `0.125` without loose helper sidecars or a
  separate runner; newly linked programs must carry the print helper trailer
  bytes that `ALINK` selects,
  `X=A/B` with `A=1.5`, `B=1.5` producing `1`, and
  `X=A/B` with `A=1.5`, `B=0.75` producing `2`,
  `X=A/B` with `A=1.0`, `B=3.0` producing `0.3333333432674407958984375`,
  `X=A/B` with `A=1.0`, `B=9.0` producing `0.111111111938953399658203125`,
  `X=A/B` with `A=2.0`, `B=9.0` producing `0.22222222387790679931640625`,
  `X=A/B` with `A=1.0`, `B=11.0` producing `0.0909090936183929443359375`,
  `X=A/B` with `A=2.0`, `B=11.0` producing `0.181818187236785888671875`,
  `X=A/B` with `A=1.0`, `B=13.0` producing `0.076923079788684844970703125`,
  `X=A/B` with `A=2.0`, `B=13.0` producing `0.15384615957736968994140625`,
  `X=A/B` with `A=2.0`, `B=3.0` producing `0.666666686534881591796875`,
  `X=A/B` with `A=1.0`, `B=7.0` producing `0.14285714924335479736328125`,
  `X=A/B` with `A=1.0`, `B=10.0` producing `0.100000001490116119384765625`,
  `X=A+B` with `A=(1.0/10.0)`, `B=(1.0/5.0)` producing
  `0.300000011920928955078125`,
  `X=A+B` with `X=(1.0/10.0)+(1.0/5.0)` and `B=(1.0/5.0)` producing `0.5`,
  `X=A-B` with `A=(1.0/2.0)`, `B=(1.0/10.0)` producing
  `0.4000000059604644775390625`,
  `X=X-C` after `X=(1.0/10.0)+(1.0/10.0)` and `C=(1.0/5.0)` producing `0`,
  `X=(A+B+A)*10` after `A=(1.0/10.0)` and `B=(1.0/10.0)` producing `3`,
  `X=A+B` with `A=(2.0/13.0)` and `B=(1.0/13.0)` producing
  `0.2307692468166351318359375`,
  `X=A+B` with `A=(2.0/17.0)` and `B=(1.0/17.0)` producing
  `0.17647059261798858642578125`,
  `X=A+B` with `A=(2.0/19.0)` and `B=(1.0/19.0)` producing
  `0.15789473056793212890625`,
  `X=A+B` with `A=(2.0/23.0)` and `B=(1.0/23.0)` producing
  `0.1304347813129425048828125`,
  `X=A*B` with `A=(1.0/7.0)`, `B=7.0` producing `1`,
  `X=A*B` with `A=(1.0/9.0)`, `B=9.0` producing `1`,
  `X=A*B` with `A=(1.0/11.0)`, `B=11.0` producing `1`,
  `X=A*B` with `A=(1.0/13.0)`, `B=13.0` producing `1`,
  `X=A*B` with `A=(1.0/17.0)`, `B=17.0` producing `1`,
  `X=A*B` with `A=(1.0/19.0)`, `B=19.0` producing `1`,
  `X=A*B` with `A=(1.0/23.0)`, `B=23.0` producing `1`,
  `X=A*B` with `A=(1.0/5.0)`, `B=(1.0/5.0)` producing
  `0.0400000028312206268310546875`,
  `X=A/B` with `A=(1.0/10.0)`, `B=(1.0/5.0)` producing `0.5`,
  `X=A/B` with `A=(1.0/17.0)`, `B=(2.0/17.0)` producing `0.5`,
  `X=A/B` with `A=(1.0/19.0)`, `B=(2.0/19.0)` producing `0.5`,
  `X=A/B` with `A=(1.0/23.0)`, `B=(2.0/23.0)` producing `0.5`,
  `X=A/B` with `A=(6.0/5.0)`, `B=(3.0/10.0)` producing `4`, and
  `X=A*B` with `A=(1.0/3.0)`, `B=3.0` producing `1`,
  `X=A*B` with `A=(1.0/10.0)`, `B=10.0` producing `1`,
  `X=A/B` with `A=1.0`, `B=17.0` producing `0.0588235296308994293212890625`,
  `X=A/B` with `A=2.0`, `B=17.0` producing
  `0.117647059261798858642578125`,
  `X=A/B` with `A=1.0`, `B=19.0` producing `0.052631579339504241943359375`,
  `X=A/B` with `A=2.0`, `B=19.0` producing
  `0.10526315867900848388671875`,
  `X=A/B` with `A=1.0`, `B=23.0` producing `0.0434782616794109344482421875`,
  and `X=A/B` with `A=2.0`, `B=23.0` producing
  `0.086956523358821868896484375`.
- `rt_sid_freq.obj` sets a SID voice frequency word. It expects the voice index
  in `A`, frequency low byte in `X`, and frequency high byte in `Y`; it stores
  to `$D400+7*voice` and `$D401+7*voice`, then returns with `RTS`.
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
- `rt_sid_ad.obj` sets a SID voice attack/decay byte. It expects the voice
  index in `A` and the attack/decay byte in `Y`; it stores to
  `$D405+7*voice`, then returns with `RTS`.
- `rt_sid_sr.obj` sets a SID voice sustain/release byte. It expects the voice
  index in `A` and the sustain/release byte in `Y`; it stores to
  `$D406+7*voice`, then returns with `RTS`.
- `rt_sid_vol.obj` sets the SID master volume nybble. It expects the volume in
  `A`, masks it to four bits, stores `$D418`, and returns with `RTS`.
- `rt_sprite_on.obj` is the first target-side SID/sprite helper implemented as
  machine code. It expects a sprite index in `A`, sets the matching enable bit
  in VIC-II register `$D015`, and returns with `RTS`; the ALINK direct-PRG
  probe proves the helper is selected from `LIB/` and carried in the final
  linked program.
- `rt_sprite_off.obj` is the matching machine-code helper for clearing a sprite
  enable bit. It expects a sprite index in `A`, clears the matching bit in
  `$D015`, and returns with `RTS`; the probe seeds `$D015` first so the target
  run verifies an actual bit-clear side effect.
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
- `rt_sprite_mc.obj`, `rt_sprite_xexp.obj`, `rt_sprite_yexp.obj`, and
  `rt_sprite_prio.obj` are per-sprite bit-control helpers. They expect the
  sprite index in `A` and a boolean flag in `Y`, then set or clear the matching
  bit in `$D01C`, `$D01D`, `$D017`, or `$D01B` respectively.
- `rt_sprite_set_mc.obj` sets the shared multicolor sprite registers. It
  expects multicolor 0 in `A` and multicolor 1 in `X`, stores to `$D025` and
  `$D026`, and returns with `RTS`.
