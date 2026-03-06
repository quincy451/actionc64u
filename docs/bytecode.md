# ActionC64U `.avm` Bytecode Format

## Version 1 Header

All multibyte integers are little-endian.

| Offset | Size | Field |
| --- | ---: | --- |
| 0 | 4 | Magic = `AVM1` |
| 4 | 1 | Format version = `1` |
| 5 | 2 | Payload length |
| 7 | 2 | Entry offset |
| 9 | 1 | Flags (reserved, currently `0`) |
| 10 | N | Payload bytes |

Header size is fixed at 10 bytes.

## Rules

- `payload length` is the exact byte count of the Acheron instruction stream.
- `entry offset` is the byte offset within the payload where execution begins.
- `flags` must be zero for version 1 readers/writers.
- Readers must reject files with the wrong magic, unsupported version, or an
  entry offset beyond the payload length.

## Stability

This format is intentionally small and stable for early bootstrapping:

- one payload
- one entry point
- no relocation table yet
- no export table yet

Future extensions can add optional trailing sections after the payload, guarded
by new version values or non-zero feature flags.

## Current Example

`examples/hello.avm` is a tiny placeholder payload built from the manual opcode
subset we currently know (`calln` and `native`). It is enough to exercise the
packer and header validation even before the full CP/M-65 runner is automated.
