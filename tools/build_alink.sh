#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
SRC="$ROOT_DIR/src/tools_cpm/alink/alink.c"
OUT_COM="$BUILD_DIR/alink.com"
LLVM_BIN="$($ROOT_DIR/tools/find_llvm_mos.sh)"
OPT_LEVEL="${ACTIONC64U_OPT_LEVEL:--Oz}"

mkdir -p "$BUILD_DIR"
"$LLVM_BIN/mos-cpm65-clang" "$OPT_LEVEL" -o "$OUT_COM" "$SRC"
echo "Built $OUT_COM"
