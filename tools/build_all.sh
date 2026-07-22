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

cd "$ROOT_DIR"

./tools/env_check.sh
require_tool git "Install git."
require_tool make "Install make."
require_tool python3 "Install python3."

if [[ -d "$ROOT_DIR/../udos" && -f "$ROOT_DIR/../Makefile" ]]; then
  (cd "$ROOT_DIR/.." && make test)
else
  ./tools/build_actc_udos.sh
  ./tools/build_alink_udos.sh
  ./tools/build_tool_abi_harness.sh
  python3 -m unittest discover -v -s tests -p 'test*.py'
fi

echo "Built maintained UDOS tools and ran tests."
