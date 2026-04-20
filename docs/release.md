# Release Disk Layout

The C64 Ultimate CP/M-65 release disk ships a bootable Commodore 1541 image
containing:

- `ccp.sys`
- `bdos.sys`
- `actmon.com`
- `actc.com`
- `vm.com`
- `bedit.com`
- `libmods.dat` packed runtime manifest bundle
- `hello.act`
- `math.act`
- `if.act`
- `realdemo.act`
- `real_cmp.act`
- `reu_demo.act`
- `ovl_demo.act`

## User Workflow

On real hardware or VICE:

1. Boot the Commodore disk:
   `LOAD "CPM",8,1`
   then `RUN`
2. Wait for the CP/M prompt: `A>`
3. Use the bundled tools:
   `ACTMON`
   `ACTC HELLO.ACT`
   `VM HELLO.AVM`

## REU Requirement

Prompt-17 release validation assumes a 16MB REU:

- C64 Ultimate target: 16MB REU enabled
- VICE target: `-reu -reusize 16384`

## Build Artifact

The release builder writes:

- `build/actionc64u_c64.d64`

and a host-side listing transcript:

- `build/actionc64u_c64.dir.txt`

## Automated VICE Verification

Run:

```sh
python3 tools/verify_release.py
```

The verifier:

- rebuilds the release image if needed
- injects a host-built `hello.avm`
- injects `$$$.sub` so CP/M autoruns `VM HELLO.AVM` after boot
- captures screen snapshots in `build/verify_transcript.txt`

The automated path uses CP/M submit-file autorun rather than live `A>` keyboard
typing, because that is the reliable path under VICE for CP/M-65 on the C64.
