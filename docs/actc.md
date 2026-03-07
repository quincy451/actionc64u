# `actc.com`

`actc.com` is the first on-target ActionC64U compiler for CP/M-65.

## Current Supported Subset

The current shipped subset matches the integer bootstrap implemented by the host
reference compiler:

- optional `MODULE <name>` header
- `PROC main()`
- local declarations: `BYTE`, `CARD`, `INT`
- assignments with compile-time expression evaluation
- arithmetic: `+`, `-`, `*`, `/`
- comparisons: `=`, `<>`, `<`, `<=`, `>`, `>=`
- `IF ... THEN ... FI`
- `Print("literal")`
- `PrintE("literal")`
- `PrintI(expr)`
- `PrintIE(expr)`
- `RETURN`

`actc.com` still emits a runnable `.avm` file directly. There is no on-target
`.avo` linker yet, so this remains a monolithic compiler for now.

## File Behavior

- input: first filename argument, default `main.act`
- output: `<stem>.avm`
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

The on-target compiler currently follows the same bootstrap rule as the host
tool: it evaluates the supported integer subset at compile time and lowers the
result to a print-only `.avm` payload. That keeps `vm.com` extremely small while
we move the toolchain onto CP/M-65.

## Limitations

- only one procedure: `main`
- no functions, arrays, pointers, records, or directives beyond optional `MODULE`
- no on-target object format or library linker yet
- output files are written in 128-byte CP/M records; `vm.com` relies on the
  `AVM1` payload length instead of host file length

## Planned Expansion

Next steps are:

- carry more of the real ACTION! surface onto CP/M-65
- move dead-strip object/link behavior on target
- locate runtime modules from disk instead of baking everything into one compiler
- eventually replace the bootstrap print-only lowering with fuller VM execution
