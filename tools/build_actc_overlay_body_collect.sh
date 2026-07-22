#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC_DIR="$ROOT_DIR/src/tools_udos/actc"
SRC="$SRC_DIR/actc_overlay_body_collect.asm"
CFG="$SRC_DIR/actc_overlay.cfg"
OBJ="$BUILD_DIR/actc_overlay_body_collect.o"
BIN="$BUILD_DIR/ACTC_OVL6.BIN"
LABELS="$BUILD_DIR/actc_overlay_body_collect.labels"
MAP="$BUILD_DIR/actc_overlay_body_collect.map"

mkdir -p "$BUILD_DIR"

ACTC_KEEP_BODY_RESIDENT_FALLBACK="${ACTC_KEEP_BODY_RESIDENT_FALLBACK:-0}"

ca65 -g -D "ACTC_KEEP_BODY_RESIDENT_FALLBACK=$ACTC_KEEP_BODY_RESIDENT_FALLBACK" -o "$OBJ" "$SRC" -I "$SRC_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$LABELS" -m "$MAP"
printf '%s\n' "$BIN"
