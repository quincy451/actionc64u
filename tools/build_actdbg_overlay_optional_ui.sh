#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC_DIR="$ROOT_DIR/src/tools_udos/actdbg"
SRC="$SRC_DIR/actdbg_overlay_optional_ui.asm"
CFG="$SRC_DIR/actdbg_overlay.cfg"
OBJ="$BUILD_DIR/actdbg_overlay_optional_ui.o"
BIN="$BUILD_DIR/ACTDBG_OVL1.BIN"
LABELS="$BUILD_DIR/actdbg_overlay_optional_ui.labels"
MAP="$BUILD_DIR/actdbg_overlay_optional_ui.map"
RESIDENT_LABELS="${ACTDBG_LABELS:-$BUILD_DIR/actdbg.current.labels}"
RESIDENT_INC="$BUILD_DIR/actdbg_overlay_resident.inc"

mkdir -p "$BUILD_DIR"

python3 "$ROOT_DIR/tools/generate_ca65_label_inc.py" \
  --labels "$RESIDENT_LABELS" \
  --output "$RESIDENT_INC" \
  --prefix ACTDBG_RES_

ca65 -g -o "$OBJ" "$SRC" -I "$SRC_DIR" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$LABELS" -m "$MAP"
printf '%s\n' "$BIN"
