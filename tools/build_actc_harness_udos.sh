#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UDOS_DIR="$ROOT_DIR/../udos"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC="$ROOT_DIR/src/tools_udos/actc/actc.asm"
CFG="$ROOT_DIR/src/tools_udos/actc/actc_harness.cfg"
LABELS="$UDOS_DIR/build/udos-resident.labels"
RELEASE_LABELS="$UDOS_DIR/build/release/udos-resident.labels"
INC="$BUILD_DIR/udos_services.inc"
OBJ="$BUILD_DIR/actc_harness.o"
BIN="$BUILD_DIR/actc_harness.bin"
PRG="$BUILD_DIR/ACTC_HARNESS.PRG"
CURRENT_LABELS="$BUILD_DIR/actc_harness.current.labels"
CURRENT_MAP="$BUILD_DIR/actc_harness.current.map"
ACTC_BODY_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_body_collect.sh"
ACTC_KEEP_BODY_RESIDENT_FALLBACK="${ACTC_KEEP_BODY_RESIDENT_FALLBACK:-0}"
ACTC_ENABLE_REAL_CONST_EVALUATOR="${ACTC_ENABLE_REAL_CONST_EVALUATOR:-1}"

mkdir -p "$BUILD_DIR"

python3 "$ROOT_DIR/tools/generate_actc_real_const_runtime.py" \
  --output "$BUILD_DIR/actc_real_const_runtime.inc" >/dev/null

if [[ -n "${UDOS_LABELS:-}" ]]; then
  LABELS="$UDOS_LABELS"
elif [[ -f "$RELEASE_LABELS" ]]; then
  LABELS="$RELEASE_LABELS"
elif [[ ! -f "$LABELS" ]]; then
  make -C "$UDOS_DIR" resident >/dev/null
fi

python3 "$ROOT_DIR/tools/generate_udos_service_inc.py" --labels "$LABELS" --output "$INC"

ca65 -g -D ACTC_USE_BODY_OVERLAY=1 -D "ACTC_KEEP_BODY_RESIDENT_FALLBACK=$ACTC_KEEP_BODY_RESIDENT_FALLBACK" -D "ACTC_ENABLE_REAL_CONST_EVALUATOR=$ACTC_ENABLE_REAL_CONST_EVALUATOR" -D SOURCE_LIMIT=511 -D BODY_OPS_STRIDE=160 -D INT_LITERAL_MAX=36 -D STRING_LITERAL_MAX=36 -D EXPORT_MAX=16 -D EXTERNAL_MAX=16 -D LOOP_MAX=16 -o "$OBJ" "$SRC" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$CURRENT_LABELS" -m "$CURRENT_MAP"
printf '\x00\x09' > "$PRG"
cat "$BIN" >> "$PRG"
ACTC_KEEP_BODY_RESIDENT_FALLBACK="$ACTC_KEEP_BODY_RESIDENT_FALLBACK" bash "$ACTC_BODY_OVERLAY_BUILD" >/dev/null
printf '%s\n' "$PRG"
