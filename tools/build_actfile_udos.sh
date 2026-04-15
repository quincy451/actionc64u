#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UDOS_DIR="$ROOT_DIR/../udos"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC="$ROOT_DIR/src/tools_udos/actfile/actfile.asm"
CFG="$ROOT_DIR/src/tools_udos/actfile/actfile.cfg"
LABELS="$UDOS_DIR/build/udos-resident.labels"
RELEASE_LABELS="$UDOS_DIR/build/release/udos-resident.labels"
INC="$BUILD_DIR/udos_services.inc"
OBJ="$BUILD_DIR/actfile.o"
BIN="$BUILD_DIR/actfile.bin"
PRG="$BUILD_DIR/ACTFILE.PRG"

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
printf '\x00\x09' > "$PRG"
cat "$BIN" >> "$PRG"
printf '%s\n' "$PRG"
