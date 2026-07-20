# INPUT1 Joystick And Mouse Library

`LIB/INPUT1.ACT` documents the current C64 input helper names. ACTC recognizes
these names directly, emits imports for the helpers that are actually used, and
ALINK links only the referenced `RT_*.OBJ` modules into the final PRG.

Joystick helpers:

- `Joy(port)` returns an active-high bitfield for control port `1` or `2`.
- `JoySeen(port)` returns `1` after observed joystick activity, otherwise `0`.
- `JoyBtn1(port)` returns `1` when joystick button 1 is active, otherwise `0`.
- `JoyBtn2(port)` returns `1` when joystick button 2 is active, otherwise `0`.

`JOY_BUTTON2` follows the Commodore 64GS convention: the second fire button is
connected to control-port pin 9 (POTX). The helper selects the requested
control port through CIA1 before sampling the SID POTX register.

Joystick bits:

- `JOY_UP = $01`
- `JOY_DOWN = $02`
- `JOY_LEFT = $04`
- `JOY_RIGHT = $08`
- `JOY_BUTTON1 = $10`
- `JOY_BUTTON2 = $20`

Mouse helpers:

- `MousePoll(port)` samples the selected control port, updates mouse state, and
  returns inferred presence.
- `MouseSeen()` returns the last inferred mouse presence state.
- `MouseX()` returns the accumulated 8-bit X position.
- `MouseY()` returns the accumulated 8-bit Y position.
- `MouseBtn()` returns the button bitfield.
- `MouseBtn1()` returns `1` when mouse button 1 is active, otherwise `0`.
- `MouseBtn2()` returns `1` when mouse button 2 is active, otherwise `0`.

The mouse helpers implement Commodore 1351 proportional mode. Button 1 is the
control-port FIRE line and button 2 is the UP line. `MousePoll` selects the
requested control port, waits for the SID paddle conversion to settle, ignores
the POT noise and don't-care bits, and accumulates signed modulo-64 movement.
`MouseY` follows C64 screen coordinates, increasing downward.
Port 1 and port 2 keep independent position and inferred-presence state; the
no-argument accessors report the port selected by the most recent poll.

Mouse bits:

- `MOUSE_BUTTON1 = $01`
- `MOUSE_BUTTON2 = $02`

Presence caveats:

- A passive C64 joystick cannot be reliably detected while idle.
- Mouse presence is inferred from observed movement or button activity.
- These helpers report observed state, not a hard electrical guarantee that a
  device is attached.
