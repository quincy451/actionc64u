# CP/M Disk Layout

ActionC64U currently uses flat CP/M filenames instead of subdirectories. The
same layout works on CP/M-65 and under `cpmemu`, which only exposes lowercase
8.3 host filenames.

## Tool Files

- `actmon.com`
- `actc.com`
- `vm.com`

Under `cpmemu`, `actmon.com` uses embedded compile/run entry points for
`COMPILE`, `RUN`, and `BUILD` because direct COM launches do not provide a CCP
handoff path for running additional tools. On a fuller CP/M-65 system, `EDIT`
can still chain to an external editor when `SUBMIT`/`CCP` support is present.

## Library Manifests

CP/M-65 does not give us a portable `LIB/` directory in this workflow, so the
bootstrap toolchain uses filename prefixes instead:

- `libpstr.mod` -> `rt.print_str`
- `libplin.mod` -> `rt.print_line`
- `libfint.mod` -> `rt.format_int`

Each manifest lives on disk and is read by `actc.com` during compile time. The
compiler starts from the main program's logical imports, follows manifest
imports recursively, emits a single runnable `.avm`, and writes a sidecar
`.map` describing exactly which modules were included.

## Example Working Set

A minimal staged drive for current development contains:

- `actmon.com`
- `actc.com`
- `vm.com`
- `libpstr.mod`
- `libplin.mod`
- `libfint.mod`
- `hello.act`
- `math.act`
- `if.act`
