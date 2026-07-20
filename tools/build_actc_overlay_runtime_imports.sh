#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC_DIR="$ROOT_DIR/src/tools_udos/actc"
SRC="$SRC_DIR/actc_overlay_runtime_imports.asm"
CFG="$SRC_DIR/actc_overlay.cfg"
OBJ="$BUILD_DIR/actc_overlay_runtime_imports.o"
BIN="$BUILD_DIR/ACTC_OVL4.BIN"
LABELS="$BUILD_DIR/actc_overlay_runtime_imports.labels"
MAP="$BUILD_DIR/actc_overlay_runtime_imports.map"

mkdir -p "$BUILD_DIR"

ca65 -g -o "$OBJ" "$SRC" -I "$SRC_DIR" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$LABELS" -m "$MAP"
printf '%s\n' "$BIN"
