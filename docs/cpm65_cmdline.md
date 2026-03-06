# CP/M-65 Command-Line Notes

These notes come from the adjacent `../cpm65-u64/src/ccp.S` and existing tools
such as `dump.asm`, `copy.c`, and `attr.c`.

## What CP/M-65 Gives a Program

When CP/M-65 launches a `.com` program, the CCP does two useful things:

- it parses the first two filename-like parameters into `cpm_fcb` and
  `cpm_fcb2`
- it copies the raw command tail into the program PBLOCK after the XFCB area

In assembly, many tools simply inspect `cpm_fcb` directly. Example pattern:

```asm
lda cpm_fcb + 1
cmp #' '
beq no_filename
```

That is enough to detect whether the first filename slot is empty.

## Practical Rule for ActionC64U Tools

For `vm.com` / `vmrun.com` we plan to use this policy:

- if `cpm_fcb` contains a filename, use it
- otherwise default to `main.avm`

This keeps the CP/M UX simple and avoids having to hand-parse arbitrary option
syntax in the first bootstrap versions.

## Raw Command Tail

`../cpm65-u64/src/ccp.S` shows that the CCP stores a length byte followed by the
raw command characters in the program PBLOCK after the XFCB area. That means we
can later support richer flags by reading the raw tail instead of relying only
on `cpm_fcb`.

## File Access Pattern

The adjacent CP/M-65 tools use the same BDOS sequence repeatedly:

1. populate or parse an FCB
2. clear `FCB_CR` before open when needed
3. set DMA to `cpm_default_dma`
4. call `BDOS_OPEN_FILE`
5. call `BDOS_READ_SEQUENTIAL` until EOF

That is the pattern the staged `vmrun` program will follow for loading `.avm`
files.
