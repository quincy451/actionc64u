#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC="$ROOT_DIR/tools/tool_abi_harness.c"
LIB6502_DIR="$ROOT_DIR/third_party/lib6502"
OUT="$BUILD_DIR/tool_abi_harness"
HARNESS_OBJ="$BUILD_DIR/tool_abi_harness.o"
LIB6502_OBJ="$BUILD_DIR/lib6502.o"

mkdir -p "$BUILD_DIR"

cc -std=c99 -O2 -Wall -Wextra \
  -I"$LIB6502_DIR" \
  -c "$SRC" \
  -o "$HARNESS_OBJ"

cc -std=c99 -O2 -Wall -Wextra -Wno-unused-function \
  -I"$LIB6502_DIR" \
  -c "$LIB6502_DIR/lib6502.c" \
  -o "$LIB6502_OBJ"

cc "$HARNESS_OBJ" "$LIB6502_OBJ" -o "$OUT"

printf '%s\n' "$OUT"
