#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UDOS_DIR="$ROOT_DIR/../udos"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC="$ROOT_DIR/src/tools_udos/actmon/actmon.asm"
CFG="$ROOT_DIR/src/tools_udos/actmon/actmon.cfg"
LABELS="$UDOS_DIR/build/udos-resident.labels"
RELEASE_LABELS="$UDOS_DIR/build/release/udos-resident.labels"
INC="$BUILD_DIR/udos_services.inc"
OBJ="$BUILD_DIR/actmon.o"
BIN="$BUILD_DIR/actmon.bin"
PRG="$BUILD_DIR/ACTMON.PRG"

mkdir -p "$BUILD_DIR"

if [[ -n "${UDOS_LABELS:-}" ]]; then
  LABELS="$UDOS_LABELS"
elif [[ -f "$RELEASE_LABELS" ]]; then
  LABELS="$RELEASE_LABELS"
elif [[ ! -f "$LABELS" ]]; then
  make -C "$UDOS_DIR" resident >/dev/null
fi

python3 "$ROOT_DIR/tools/generate_udos_service_inc.py" --labels "$LABELS" --output "$INC"

ca65 -g -o "$OBJ" "$SRC" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ"
python3 - "$CFG" "$BIN" "$PRG" <<'PY'
from pathlib import Path
import re
import sys

cfg_path = Path(sys.argv[1])
bin_path = Path(sys.argv[2])
prg_path = Path(sys.argv[3])
cfg_text = cfg_path.read_text(encoding="ascii")
match = re.search(r"CODE:\s+start\s*=\s*\$([0-9A-Fa-f]+)", cfg_text)
if not match:
    raise SystemExit(f"could not find CODE start address in {cfg_path}")
load_addr = int(match.group(1), 16)
prg_path.write_bytes(bytes((load_addr & 0xFF, (load_addr >> 8) & 0xFF)) + bin_path.read_bytes())
PY
printf '%s\n' "$PRG"
