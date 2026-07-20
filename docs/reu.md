# ActionC64U Application REU Model

## Product Boundary

Application REU storage is generated-program behavior, not an operating-system
service. The link-selected `rt_reu_*` OBJ1 modules access C64 REU hardware
directly and are shared with the Idun fork. They must remain absent from a
linked PRG unless the source references an REU operation.

Idun ACTC currently lowers this source surface:

```action
REU BYTE ARRAY big(50000)
ReuPoke8(big,0,65)
ReuPoke16(big,2,1234)
ReuPeek8(big,0)
ReuPeek16(big,2)
```

Native `ACTC.PRG` does not yet parse the declaration or lower the accessors.
Its own use of REU for source windows, metadata tables, and compiler overlays
is an implementation detail and does not provide application-level parity.
The native `examples/reu_demo.act` file is therefore a porting fixture until
that compiler work lands.

## Native Delivery

1. Parse bounded global and local `REU BYTE ARRAY name(constant-size)`
   declarations using the common compiler-constant layer.
2. Allocate handles at `MAIN` entry or local declaration points through the
   existing link-selected modules.
3. Lower 8/16-bit peek and poke expressions/calls, reject dynamic or out-of-
   range declaration sizes, and preserve little-endian values.
4. Prove helper closure and bounds behavior in host-oracle tests and a direct
   ACTC/ALINK/VICE PRG. No UDOS resident call or runtime runner may be added.
5. Record physical REU results using the UDOS hardware-validation runbook.

The initial maintained surface remains byte arrays and 8/16-bit access. Wider
peek/poke and copy operations can be exposed only after their source ABI and
target tests are defined.
