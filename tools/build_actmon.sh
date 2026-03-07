#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build"
SRC="$ROOT_DIR/src/tools_cpm/actmon/actmon.c"
ACTC_SRC="$ROOT_DIR/src/tools_cpm/actc/actc.c"
VM_SRC="$ROOT_DIR/src/vm/vmrun/vm.c"
ACTC_OBJ="$BUILD_DIR/actc_lib.o"
VM_OBJ="$BUILD_DIR/vm_lib.o"
OUT_COM="$BUILD_DIR/actmon.com"
LLVM_BIN="$($ROOT_DIR/tools/find_llvm_mos.sh)"

mkdir -p "$BUILD_DIR"
"$LLVM_BIN/mos-cpm65-clang" -Os -DACTC_LIBRARY -c -o "$ACTC_OBJ" "$ACTC_SRC"
"$LLVM_BIN/mos-cpm65-clang" -Os -DVM_LIBRARY -c -o "$VM_OBJ" "$VM_SRC"
"$LLVM_BIN/mos-cpm65-clang" -Os -o "$OUT_COM" "$SRC" "$ACTC_OBJ" "$VM_OBJ"
echo "Built $OUT_COM"
