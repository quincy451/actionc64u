#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC_DIR="$ROOT_DIR/src/tools_udos/actedit"
SRC="$SRC_DIR/actedit_overlay_mutation.asm"
CFG="$SRC_DIR/actedit_overlay.cfg"
OBJ="$BUILD_DIR/actedit_overlay_mutation.o"
BIN="$BUILD_DIR/ACTEDIT_OVL1.BIN"
LABELS="$BUILD_DIR/actedit_overlay_mutation.labels"
MAP="$BUILD_DIR/actedit_overlay_mutation.map"
RESIDENT_LABELS="${ACTEDIT_LABELS:-$BUILD_DIR/actedit.current.labels}"
RESIDENT_INC="$BUILD_DIR/actedit_overlay_resident.inc"

mkdir -p "$BUILD_DIR"

python3 "$ROOT_DIR/tools/generate_ca65_label_inc.py" \
  --labels "$RESIDENT_LABELS" \
  --output "$RESIDENT_INC" \
  --prefix ACTEDIT_RES_

ca65 -g -o "$OBJ" "$SRC" -I "$SRC_DIR" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$LABELS" -m "$MAP"
printf '%s\n' "$BIN"
