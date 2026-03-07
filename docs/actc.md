# `actc.com`

`actc.com` is the first on-target ActionC64U compiler for CP/M-65.

## Current Supported Subset

The current shipped subset matches the bootstrap on-target evaluator:

- optional `MODULE <name>` header
- optional `OVERLAY <name> ... ENDOVERLAY` blocks before `PROC main()`
- `PROC main()`
- local declarations: `BYTE`, `CARD`, `INT`, `REAL`
- far declarations: `REU BYTE ARRAY name(length)`
- assignments with compile-time expression evaluation
- arithmetic: `+`, `-`, `*`, `/`
- comparisons: `=`, `<>`, `<`, `<=`, `>`, `>=`
- `IF ... THEN ... FI`
- `Print("literal")`
- `PrintE("literal")`
- `PrintI(expr)`
- `PrintIE(expr)`
- `PrintR(expr)`
- `PrintRE(expr)`
- `REAL(x)` / `INT(r)` conversions
- `ReuPoke8`, `ReuPoke16`, `ReuPeek8`, `ReuPeek16`
- `OverlayCall(name)`
- `RETURN`

`actc.com` still emits a runnable `.avm` file directly. There is no on-target
`.avo` linker yet, so this remains a monolithic compiler for now.

## File Behavior

- input: first filename argument, default `main.act`
- output: `<stem>.avm` plus `<stem>.map`
- filenames should stay lowercase 8.3 when running under `cpmemu`

`actc.com` reads the source through CP/M BDOS sequential file calls and writes a
monolithic `AVM1` file that `vm.com` can execute.

## `vm.com`

The CP/M runner currently validates the `AVM1` header and interprets the small
opcode subset used by the bootstrap compiler:

- `setp16`
- `calln 0xff00` (`Print`)
- `calln 0xff10` (`PrintE`)
- `calln 0xff20` (`Exit`)

## Semantics

The on-target compiler still follows the bootstrap rule used by the host
reference compiler: it evaluates the currently supported subset at compile time
and lowers the result to a print-oriented `.avm` payload. REAL arithmetic,
simulated REU access, and overlay bodies are all resolved in the compiler today,
while logical runtime imports are still emitted into the map/dead-strip flow.

## Limitations

- only one procedure: `main`
- no functions, pointers, records, or directives beyond optional `MODULE`
- `actmon.com` embeds a prompt-15-sized compiler subset; the full prompt-16
  feature set is currently in standalone `actc.com`
- output files are written in 128-byte CP/M records; `vm.com` relies on the
  `AVM1` payload length instead of host file length

## Planned Expansion

Next steps are:

- carry more of the real ACTION! surface onto CP/M-65
- move dead-strip object/link behavior on target
- locate runtime modules from disk instead of baking everything into one compiler
- eventually replace the bootstrap print-only lowering with fuller VM execution
