#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UDOS_DIR="$ROOT_DIR/../udos"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC="$ROOT_DIR/src/tools_udos/actc/actc.asm"
CFG="$ROOT_DIR/src/tools_udos/actc/actc_harness.cfg"
LABELS="$UDOS_DIR/build/udos-resident.labels"
RELEASE_LABELS="$UDOS_DIR/build/release/udos-resident.labels"
INC="$BUILD_DIR/udos_services.inc"
OBJ="$BUILD_DIR/actc.o"
BIN="$BUILD_DIR/actc.bin"
PRG="$BUILD_DIR/ACTC.PRG"
CURRENT_LABELS="$BUILD_DIR/actc.current.labels"
CURRENT_MAP="$BUILD_DIR/actc.current.map"

mkdir -p "$BUILD_DIR"

if [[ -n "${UDOS_LABELS:-}" ]]; then
  LABELS="$UDOS_LABELS"
elif [[ -f "$RELEASE_LABELS" ]]; then
  LABELS="$RELEASE_LABELS"
elif [[ ! -f "$LABELS" ]]; then
  make -C "$UDOS_DIR" resident >/dev/null
fi

python3 "$ROOT_DIR/tools/generate_udos_service_inc.py" --labels "$LABELS" --output "$INC"

ca65 -g -D SOURCE_LIMIT=511 -D BODY_OPS_STRIDE=96 -D INT_LITERAL_MAX=36 -D STRING_LITERAL_MAX=36 -D EXPORT_MAX=16 -D EXTERNAL_MAX=16 -D LOOP_MAX=16 -o "$OBJ" "$SRC" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$CURRENT_LABELS" -m "$CURRENT_MAP"
printf '\x00\x09' > "$PRG"
cat "$BIN" >> "$PRG"
printf '%s\n' "$PRG"
