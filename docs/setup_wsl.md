# WSL Setup Notes

ActionC64U is developed from WSL2 against the Windows-mounted workspace at
`/mnt/c/test/action`.

## Codex CLI in WSL2

If Codex CLI is not already available in WSL, install Node.js first and then
install the package used on this machine:

```bash
npm install -g @openai/codex
codex --version
codex --help
```

If you manage Node.js with `nvm`, install the package inside the same WSL shell
environment you plan to use for this repo.

## Local Adjacent Repos Expected

- `../cpm65-u64`
- `../acheronvm`
- `../action.pdf`

Validate these paths with:

```bash
python3 tools/path_probe.py
```

## Base Tooling

Required for the current bootstrap:

- `git`
- `make`
- `python3`
- `python3-pip`
- one C compiler toolchain: GNU (`gcc`/`g++`) or LLVM/Clang (`clang`/`clang++`)

Useful now or in later prompts:

- `cmake`
- `poppler-utils` for `pdftotext`
- `cpmtools`
- `cc1541`
- `vice`
- `expect`, `socat`, or `nc`
- `java`

## Suggested Install Flow

Print the recommended WSL2 install commands without changing the system:

```bash
./tools/setup_wsl.sh
```

If you intentionally want the script to run `apt-get`, invoke it yourself under
`sudo`:

```bash
sudo ./tools/setup_wsl.sh --run
```

The script does not install `llvm-mos` automatically. The adjacent
`../cpm65-u64/Makefile` defaults `LLVM` to `/opt/pkg/llvm-mos/bin`, and the
project README documents building with:

```bash
make LLVM=/path/to/llvm-mos/bin/
```

For CP/M-65 itself, the local README also calls out these Debian/Ubuntu
packages as useful build dependencies:

- `cc1541`
- `cpmtools`
- `libfmt-dev`
- `fp-compiler`
- `moreutils`
- `mame`
- `srecord`
- `64tass`
- `libreadline-dev`

Install `pytest` explicitly if you want the full external package:

```bash
python3 -m pip install --user pytest
```

This repo also includes a minimal local `python3 -m pytest` compatibility
runner so the bootstrap tests can execute in a bare environment.

## Environment Check

Run the non-destructive environment check from the repo root:

```bash
./tools/env_check.sh
```

Interpretation:

- `PASS` means the command or tool was found on `PATH`.
- `FAIL` in the `REQUIRED` column means bootstrap or local builds will be
  limited until you install that dependency.
- `FAIL` in optional rows is advisory for later prompts.

Use strict mode when you want the script to fail the shell on missing required
dependencies:

```bash
./tools/env_check.sh --strict
```
