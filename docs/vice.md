# VICE Harness Notes

## Local Status In This Workspace

- `x64sc` was found on `PATH` at `/usr/bin/x64sc`
- no `c64*.d64` CP/M-65 disk image is currently present under
  `../cpm65-u64/images`, so the automated VICE test path will skip here until
  that image is built

## Installing VICE In WSL2

Typical Debian/Ubuntu path:

```sh
sudo apt update
sudo apt install vice
```

Then confirm:

```sh
x64sc -help
```

## Important `x64sc` Flags

Discovered from local `x64sc -help`:

- REU enable: `-reu`
- REU size: `-reusize 16384`
- remote text monitor: `-remotemonitor -remotemonitoraddress <addr>`
- binary monitor: `-binarymonitor -binarymonitoraddress <addr>`
- keyboard injection: `-keybuf <string>`
- keyboard pacing: `-keybuf-delay <value>`
- attach disk image: `-8 <path>`
- force 1541 drive type: `-drive8type 1541`
- enable true drive emulation: `-drive8truedrive`
- disable virtual device shortcuts: `+virtualdev8`

For the 16MB REU target, the harness uses:

```text
-reu -reusize 16384
```

## How Automation Works

The harness in [tools/vice_harness.py](/mnt/c/test/action/actionc64u/tools/vice_harness.py):

- finds `x64sc`
- searches `../cpm65-u64/images` for a `c64*.d64`
- launches VICE with:
  - the disk image on drive 8
  - 1541 true-drive settings
  - a 16MB REU
  - the binary monitor on a localhost TCP port
- injects `LOAD"CPM",8` and `RUN` through the monitor keyboard-feed path
- reads screen RAM `$0400-$07E7` through the monitor memory-get command
- converts the 40x25 screen buffer into ASCII-ish text for matching

The current harness uses the binary monitor because it is documented and easier
to parse reliably than scraping the interactive text monitor.

## Screen Validation

Current smoke validation target:

- wait for a stable CP/M fragment such as `A>`

Future program-run validation can feed additional keys after the prompt, for
example `HELLO`.

## Manual REU Validation

Because this workspace currently has no built `c64*.d64` CP/M image, the REU
validation path remains manual.

Once the adjacent CP/M-65 tree produces a bootable C64 image, the intended
verification sequence is:

1. Stage a host-side working set:

```sh
cd /mnt/c/test/action/actionc64u
python3 tools/install_to_image.py /tmp/actionc64u-vice
```

2. Copy the staged files onto a writable C64 CP/M disk image with `c1541`:

```sh
c1541 \
  -attach /mnt/c/test/action/cpm65-u64/images/c64cpm.d64 \
  -write /tmp/actionc64u-vice/actc.com actc.com \
  -write /tmp/actionc64u-vice/vm.com vm.com \
  -write /tmp/actionc64u-vice/reu_demo.act reu_demo.act \
  -write /tmp/actionc64u-vice/libreua.mod libreua.mod \
  -write /tmp/actionc64u-vice/librep8.mod librep8.mod \
  -write /tmp/actionc64u-vice/librpo8.mod librpo8.mod
```

3. Boot CP/M in VICE:

```sh
python3 tools/vice_harness.py --disk-image /mnt/c/test/action/cpm65-u64/images/c64cpm.d64
```

4. At the `A>` prompt, run:

```text
actc reu_demo.act
vm reu_demo.avm
```

5. Confirm the screen contains:

```text
reu ok
```

## Skip Policy

Tests skip when any prerequisite is missing:

- `x64sc` not installed
- `c64*.d64` image not built yet
- VICE fails to start or expose the monitor port cleanly
