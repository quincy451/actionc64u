#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "$*" >&2
  exit 1
}

require_tool() {
  local name="$1"
  local hint="$2"
  if ! command -v "$name" >/dev/null 2>&1; then
    fail "Missing dependency: $name. $hint"
  fi
}

require_command() {
  local hint="$1"
  shift
  if ! "$@" >/dev/null 2>&1; then
    fail "$hint"
  fi
}

cd "$ROOT_DIR"

./tools/env_check.sh
require_tool git "Install git."
require_tool make "Install make."
require_tool python3 "Install python3."
require_tool cpmcp "Install cpmtools before building the release image."
require_tool cpmls "Install cpmtools before building the release image."
require_tool cpmchattr "Install cpmtools before building the release image."
require_tool cpmrm "Install cpmtools before building the release image."
require_command "pytest is unavailable. Install it or use a Python environment where 'python3 -m pytest' works." \
  python3 -m pytest --version
require_command "llvm-mos is unavailable. See docs/setup_wsl.md and docs/blockers.md." \
  ./tools/find_llvm_mos.sh

./tools/build_actc.sh
./tools/build_vmrun.sh
./tools/build_actmon.sh
./tools/build_alink.sh
python3 -m pytest -q
python3 ./tools/install_to_image.py ./build/release_stage --no-build --clean
python3 ./tools/build_release_image.py --no-build

echo "Built tools, ran tests, and produced ./build/actionc64u_c64.d64"
