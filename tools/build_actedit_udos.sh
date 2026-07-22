#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UDOS_DIR="$ROOT_DIR/../udos"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC_DIR="$ROOT_DIR/src/tools_udos/actedit"
SRC="$SRC_DIR/actedit.asm"
CFG="$SRC_DIR/actedit.cfg"
LABELS="$UDOS_DIR/build/udos-resident.labels"
RELEASE_LABELS="$UDOS_DIR/build/release/udos-resident.labels"
INC="$BUILD_DIR/udos_services.inc"
OBJ="$BUILD_DIR/actedit.o"
BIN="$BUILD_DIR/actedit.bin"
PRG="$BUILD_DIR/ACTEDIT.PRG"
CURRENT_LABELS="$BUILD_DIR/actedit.current.labels"
CURRENT_MAP="$BUILD_DIR/actedit.current.map"
OVERLAY_BUILD="$ROOT_DIR/tools/build_actedit_overlay_mutation.sh"

mkdir -p "$BUILD_DIR"

if [[ -n "${UDOS_LABELS:-}" ]]; then
  LABELS="$UDOS_LABELS"
elif [[ -f "$RELEASE_LABELS" ]]; then
  LABELS="$RELEASE_LABELS"
elif [[ ! -f "$LABELS" ]]; then
  make -C "$UDOS_DIR" resident >/dev/null
fi

python3 "$ROOT_DIR/tools/generate_udos_service_inc.py" --labels "$LABELS" --output "$INC"

ca65 -g -o "$OBJ" "$SRC" -I "$SRC_DIR" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$CURRENT_LABELS" -m "$CURRENT_MAP"
printf '\x00\x09' > "$PRG"
cat "$BIN" >> "$PRG"
bash "$OVERLAY_BUILD" >/dev/null
printf '%s\n' "$PRG"
