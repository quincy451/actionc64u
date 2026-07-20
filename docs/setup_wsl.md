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

## Workspace Paths Expected

- `../udos`
- `docs/inspiration/action.pdf`
- `third_party/lib6502`

The host 6502 execution harness uses the vendored `lib6502` copy. No retired
compiler or operating-system tree is required by the maintained build.

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

The script does not install specialized third-party toolchains automatically.
If a later task needs one, install it separately and add it to `PATH`.

Additional optional packages sometimes useful for adjacent support tooling:

- `cc1541`
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
