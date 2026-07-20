# Optional Idun/Linux Host Tool Path

The maintained C64 product path remains the UDOS-native toolchain. On an Idun
cartridge, developer tools may additionally run as normal Linux processes on
the Raspberry Pi side while their output remains native C64 artifacts. In
particular, host `alink` writes a C64 `.PRG`; it does not produce a Linux target
program or introduce a runtime runner.

The exported Idun host workspace is self-contained and does not carry UDOS
tools. That deployment option does not retire the sibling UDOS shell, resident
services, or native `.PRG` tools. For host-generated programs intended to run
without UDOS services, required target behavior comes from selective 6502
library modules that `alink` includes only when referenced.

## Linux Host Components

The initial host suite implements file, project, compile, link, editor-index,
and debugger-sidecar workflows using Linux memory, filesystem, and process
support on Idun.

| Tool | Recommendation | Notes |
| --- | --- | --- |
| `ACTC` | Linux C++ process | Compile `SRC/<module>.ACT` into Action object records. Keep object/debug record formats stable enough for `ALINK`; remove overlay/REU capacity workarounds. |
| `ALINK` | Linux C++ process | Link native OBJ1 objects and selected 6502 runtime/helper modules into `BIN/<module>.PRG`; resolve dependencies by export rather than filename alone, retain only reachable export ranges, reject ambiguous providers, and preserve canonical source records in `BIN/<module>.DBG`. |
| `ACTEDIT` | Linux process | A full editor is better on Linux. It can edit the same project tree and invoke `ACTC`, `ALINK`, and optionally `ACTDBG`. A tiny C64 launcher is optional if the user starts it from the Commodore side. |
| `ACTNEW` | Linux process | Creates project/module skeletons and directories. |
| `ACTADD` | Linux process | Adds source modules to the project manifest. |
| `ACTWORK` | Linux process | Workspace/project summary and manifest inspection. |
| `ACTSRC` | Linux process | Source/module listing. |
| `ACTFILE` | Linux process | Source viewing/printing can be a host-side command. |
| `ACTCHK` | Linux process | Project consistency checks are host-side filesystem checks. |
| `ACT2SAVE` / `ACTSAVE` | Linux compatibility alias | The old diagnostic object-load/binary-save probe has been replaced by the Linux linker path. Keep only if compatibility command names are still useful; final `.PRG` writes belong to Linux `ALINK`. |
| `ACTINFO` | Linux process | Version/config reporting. |
| `ACTDIR` | Linux process or retired | Redundant with Linux directory listing unless retained for Action command compatibility. |
| `ACTCOPY` | Linux process or retired | Redundant with `cp`; retain only as compatibility UX. |
| `ACTDEL` | Linux process or retired | Redundant with `rm`; retain only as compatibility UX. |
| `ACTMOVE`/`ACTREN` | Linux process or retired | Redundant with `mv`; retain only as compatibility UX. |
| `ACTMKDIR` | Linux process or retired | Redundant with `mkdir`; retain only as compatibility UX. |
| `ACTRMDIR` | Linux process or retired | Redundant with `rmdir`/`rm -r`; retain only as compatibility UX. |
| `TREE.OVL` / `ACTTREE` | Linux process or retired | Directory tree walking belongs on Linux. |
| `XCOPY.OVL` | Linux process or retired | Recursive copy belongs on Linux. |
| `DELTREE.OVL` | Linux process or retired | Recursive delete belongs on Linux, with normal host-side safety prompts. |

## Hybrid Or Questionable

These need a split design rather than a straight port.

| Tool | Recommendation | Notes |
| --- | --- | --- |
| `ACTDBG` | Hybrid; C64 side remains required | Source indexing, sidecar parsing, and UI can be Linux-side eventually, but actual source-level debugging of a live C64 `.PRG` needs a Commodore-side trap/BRK/step agent or an Idun/C64 control protocol. The current implementation patches BRKs, snapshots target memory, reads registers, and restores C64 state; that cannot be replaced by a pure Linux process unless Idun exposes equivalent live machine-control APIs. |
| `ACTMON` | Likely Linux shell/front-end, unless it becomes a real C64 monitor | Current role is mostly project/workflow dispatch, so it can move host-side. If it grows into memory/register inspection of running C64 programs, that part belongs with `ACTDBG`'s C64-side agent. |
| C64 launch wrappers | Small 6502 stubs if needed | If a command is invoked from the Commodore environment but implemented on Linux, a tiny launcher/protocol shim may still be needed. The main implementation should remain the Linux executable. |

## Must Remain Commodore / 6502

These are not Linux processes in the product. They are code that runs on the
C64 or is linked into C64 programs.

| Component | Why |
| --- | --- |
| Linked user programs, `BIN/<module>.PRG` | Final Action output runs on the C64/C64U. |
| Startup/exit glue for generated PRGs | The PRG needs a C64 entry path and whatever return/cleanup convention Idun expects. |
| Runtime helpers selected by `ALINK` | Printing, integer/real math, overlays, REU allocation/copy, DBF, graphics, SID, sprite, joystick, mouse, and similar APIs must be 6502 modules linked into the PRG when used. |
| C64 hardware libraries | Anything touching VIC-II, SID, CIA, keyboard/joystick, screen RAM, color RAM, or C64 REU state belongs in 6502 code. |
| `ACTDBG` target-control agent | Breakpoints, single-step behavior, register capture, target RAM snapshots, and C64 screen capture require code running with the target machine or a cartridge protocol that has equivalent control. |
| Idun/C64 file I/O shim for host-generated programs | A generated program that runs outside UDOS and needs files must link a small 6502 library that calls the Idun/KERNAL/file API directly. |

## Host-Path Continuation Order

1. Port `ACTC` to a Linux C++ command that emits the current object/debug
   records.
2. Port `ALINK` to Linux C++ and keep direct `.PRG` plus `.DBG` output as the
   contract. Native machine OBJ1 input, filename-independent export discovery,
   export-body-specific closure and placement, canonical one-character import
   indexes, strict selected-object validation, and canonical `f`/`q`/`L`/`V`
   debug propagation are active.
3. Keep runtime/helper selection in `alink` using standalone 6502 module
   libraries for programs deployed without UDOS services.
4. Port workspace/file tools or replace them with compatibility wrappers around
   host filesystem operations.
5. Port `ACTEDIT` as a Linux editor/integrated workflow command.
6. Design `ACTDBG` as a hybrid: Linux-side source/debug UI plus a small
   Commodore-side target-control agent, unless Idun exposes a sufficient live
   machine-control API.

The authoritative UDOS verification gates remain documented in
`active_direction.md`. Host-path changes must keep those gates green when they
touch shared object formats, runtime modules, or source semantics.
