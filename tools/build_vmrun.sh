#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
SRC="$ROOT_DIR/src/vm/vmrun/vm.c"
REU_BACKEND="${ACTIONC64U_REU_BACKEND:-sim}"
REU_SRC="$ROOT_DIR/src/runtime/reu_${REU_BACKEND}.c"
REU_OBJ="$BUILD_DIR/reu_vm_${REU_BACKEND}.o"
OUT_COM="$BUILD_DIR/vm.com"
LLVM_BIN="$($ROOT_DIR/tools/find_llvm_mos.sh)"
OPT_LEVEL="${ACTIONC64U_OPT_LEVEL:-}"

mkdir -p "$BUILD_DIR"
if [[ ! -f "$REU_SRC" ]]; then
    echo "Unknown REU backend: $REU_BACKEND" >&2
    exit 1
fi
if [[ -z "$OPT_LEVEL" ]]; then
    OPT_LEVEL="-Oz"
fi
"$LLVM_BIN/mos-cpm65-clang" "$OPT_LEVEL" -c -o "$REU_OBJ" "$REU_SRC"
"$LLVM_BIN/mos-cpm65-clang" "$OPT_LEVEL" -o "$OUT_COM" "$SRC" "$REU_OBJ"
echo "Built $OUT_COM"
