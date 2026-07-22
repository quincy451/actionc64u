#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC_DIR="$ROOT_DIR/src/tools_udos/actc"
SRC="$SRC_DIR/actc_overlay_source_header.asm"
CFG="$SRC_DIR/actc_overlay_source_header.cfg"
OBJ="$BUILD_DIR/actc_overlay_source_header.o"
BIN="$BUILD_DIR/ACTC_OVL1.BIN"
LABELS="$BUILD_DIR/actc_overlay_source_header.labels"
MAP="$BUILD_DIR/actc_overlay_source_header.map"

mkdir -p "$BUILD_DIR"

if [[ ! -f "$BUILD_DIR/udos_services.inc" ]]; then
  UDOS_DIR="$ROOT_DIR/../udos"
  LABELS_FILE="$UDOS_DIR/build/release/udos-resident.labels"
  if [[ ! -f "$LABELS_FILE" ]]; then
    LABELS_FILE="$UDOS_DIR/build/udos-resident.labels"
  fi
  if [[ ! -f "$LABELS_FILE" ]]; then
    make -C "$UDOS_DIR" resident >/dev/null
  fi
  python3 "$ROOT_DIR/tools/generate_udos_service_inc.py" \
    --labels "$LABELS_FILE" --output "$BUILD_DIR/udos_services.inc"
fi

ca65 -g -o "$OBJ" "$SRC" -I "$SRC_DIR" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$LABELS" -m "$MAP"
printf '%s\n' "$BIN"
