#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC_DIR="$ROOT_DIR/src/tools_udos/actc"
SRC="$SRC_DIR/actc_overlay_emit_native_local_object.asm"
CFG="$SRC_DIR/actc_overlay.cfg"
OBJ="$BUILD_DIR/actc_overlay_emit_native_local_object.o"
BIN="$BUILD_DIR/ACTC_OVL9.BIN"
LABELS="$BUILD_DIR/actc_overlay_emit_native_local_object.labels"
MAP="$BUILD_DIR/actc_overlay_emit_native_local_object.map"

mkdir -p "$BUILD_DIR"

ca65 -g -o "$OBJ" "$SRC" -I "$SRC_DIR" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$LABELS" -m "$MAP"
printf '%s\n' "$BIN"
