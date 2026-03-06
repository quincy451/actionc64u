#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BLOCKERS_DOC="$ROOT_DIR/docs/blockers.md"
OUT_COM="$ROOT_DIR/build/vm.com"

# Reuse the same blocker discovery as vmhello for now.
if ! "$ROOT_DIR/tools/build_vmhello.sh" >/dev/null 2>&1; then
  echo "vmrun shares the current Acheron/CP-M build blockers. See $BLOCKERS_DOC." >&2
  rm -f "$OUT_COM"
  exit 2
fi

cat >&2 <<'EOF_MSG'
All external prerequisites are present, but the automated vm.com link/load path
is not finalized in this repo yet. See docs/blockers.md.
EOF_MSG
rm -f "$OUT_COM"
exit 2
