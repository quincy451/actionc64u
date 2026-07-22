#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UDOS_DIR="$ROOT_DIR/../udos"
BUILD_DIR="$ROOT_DIR/build/udos_tools"
SRC="$ROOT_DIR/src/tools_udos/actc/actc.asm"
CFG="$ROOT_DIR/src/tools_udos/actc/actc.cfg"
LABELS="$UDOS_DIR/build/udos-resident.labels"
RELEASE_LABELS="$UDOS_DIR/build/release/udos-resident.labels"
INC="$BUILD_DIR/udos_services.inc"
OBJ="$BUILD_DIR/actc.o"
BIN="$BUILD_DIR/actc.bin"
PRG="$BUILD_DIR/ACTC.PRG"
CURRENT_LABELS="$BUILD_DIR/actc.current.labels"
CURRENT_MAP="$BUILD_DIR/actc.current.map"
ACTC_USE_DECL_OVERLAY="${ACTC_USE_DECL_OVERLAY:-1}"
ACTC_USE_SOURCE_HEADER_OVERLAY="${ACTC_USE_SOURCE_HEADER_OVERLAY:-1}"
ACTC_USE_LAYOUT_OVERLAY="${ACTC_USE_LAYOUT_OVERLAY:-1}"
ACTC_USE_IMPORT_OVERLAY="${ACTC_USE_IMPORT_OVERLAY:-1}"
ACTC_USE_EMIT_OVERLAY="${ACTC_USE_EMIT_OVERLAY:-1}"
ACTC_USE_BODY_OVERLAY="${ACTC_USE_BODY_OVERLAY:-1}"
ACTC_KEEP_BODY_RESIDENT_FALLBACK="${ACTC_KEEP_BODY_RESIDENT_FALLBACK:-0}"
ACTC_ENABLE_REAL_CONST_EVALUATOR="${ACTC_ENABLE_REAL_CONST_EVALUATOR:-1}"
ACTC_PREALLOCATE_BODY_EXTERNALS="${ACTC_PREALLOCATE_BODY_EXTERNALS:-1}"
ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY="${ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY:-1}"
ACTC_SOURCE_WINDOW="${ACTC_SOURCE_WINDOW:-1280}"
ACTC_SOURCE_LOOKAHEAD="${ACTC_SOURCE_LOOKAHEAD:-255}"
ACTC_SOURCE_HEADER_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_source_header.sh"
ACTC_PREPROCESS_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_preprocess.sh"
ACTC_WORKFLOW_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_noop.sh"
ACTC_DECL_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_decl_counts.sh"
ACTC_LAYOUT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_payload_layout.sh"
ACTC_IMPORT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_runtime_imports.sh"
ACTC_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_object.sh"
ACTC_NATIVE_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_object.sh"
ACTC_NATIVE_LOCAL_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_local_object.sh"
ACTC_NATIVE_REAL_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_real_object.sh"
ACTC_NATIVE_REAL_CONTROL_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_real_control_object.sh"
ACTC_NATIVE_REAL_WHILE_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_real_while_object.sh"
ACTC_NATIVE_RUNTIME_CONDITION_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_runtime_condition_object.sh"
ACTC_NATIVE_RUNTIME_SEQUENCE_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_runtime_sequence_object.sh"
ACTC_NATIVE_RUNTIME_NESTED_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_runtime_nested_object.sh"
ACTC_NATIVE_LOCAL_RUNTIME_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_local_runtime_object.sh"
ACTC_NATIVE_LOCAL_MIXED_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_local_mixed_object.sh"
ACTC_NATIVE_FIXED_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_fixed_object.sh"
ACTC_NATIVE_REAL_FUNCTION_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_real_function_object.sh"
ACTC_NATIVE_REAL_POSTFIX_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_real_postfix_object.sh"
ACTC_NATIVE_REAL_POSTFIX_CONTROL_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_real_postfix_control_object.sh"
ACTC_NATIVE_REAL_POSTFIX_MULTI_CONTROL_EMIT_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_emit_native_real_postfix_multi_control_object.sh"
ACTC_BODY_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_body_collect.sh"
ACTC_PREALLOC_OVERLAY_BUILD="$ROOT_DIR/tools/build_actc_overlay_body_preallocate.sh"

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

ca65 -g -D ACTC_REU_SOURCE_CACHE=1 -D "ACTC_USE_DECL_OVERLAY=$ACTC_USE_DECL_OVERLAY" -D "ACTC_USE_SOURCE_HEADER_OVERLAY=$ACTC_USE_SOURCE_HEADER_OVERLAY" -D "ACTC_USE_LAYOUT_OVERLAY=$ACTC_USE_LAYOUT_OVERLAY" -D "ACTC_USE_IMPORT_OVERLAY=$ACTC_USE_IMPORT_OVERLAY" -D "ACTC_USE_EMIT_OVERLAY=$ACTC_USE_EMIT_OVERLAY" -D "ACTC_USE_BODY_OVERLAY=$ACTC_USE_BODY_OVERLAY" -D "ACTC_KEEP_BODY_RESIDENT_FALLBACK=$ACTC_KEEP_BODY_RESIDENT_FALLBACK" -D "ACTC_ENABLE_REAL_CONST_EVALUATOR=$ACTC_ENABLE_REAL_CONST_EVALUATOR" -D "ACTC_PREALLOCATE_BODY_EXTERNALS=$ACTC_PREALLOCATE_BODY_EXTERNALS" -D "ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY=$ACTC_PREALLOCATE_BODY_EXTERNALS_IN_OVERLAY" -D STREAM_OUTPUT=1 -D CONTENT_BUFFER_SIZE=16 -D OUTPUT_CHUNK_SIZE=128 -D "SOURCE_LIMIT=$ACTC_SOURCE_WINDOW" -D "SOURCE_LOOKAHEAD=$ACTC_SOURCE_LOOKAHEAD" -D BODY_OPS_STRIDE=255 -D INT_LITERAL_MAX=36 -D STRING_LITERAL_MAX=36 -D EXPORT_MAX=16 -D EXTERNAL_MAX=36 -D LOOP_MAX=16 -o "$OBJ" "$SRC" -I "$BUILD_DIR"
ld65 -C "$CFG" -o "$BIN" "$OBJ" -Ln "$CURRENT_LABELS" -m "$CURRENT_MAP"
printf '\x00\x09' > "$PRG"
cat "$BIN" >> "$PRG"
bash "$ACTC_WORKFLOW_OVERLAY_BUILD" >/dev/null
if [[ "$ACTC_USE_SOURCE_HEADER_OVERLAY" != "0" ]]; then
  bash "$ACTC_SOURCE_HEADER_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_PREPROCESS_OVERLAY_BUILD" >/dev/null
fi
if [[ "$ACTC_USE_DECL_OVERLAY" != "0" ]]; then
  bash "$ACTC_DECL_OVERLAY_BUILD" >/dev/null
fi
if [[ "$ACTC_USE_LAYOUT_OVERLAY" != "0" ]]; then
  bash "$ACTC_LAYOUT_OVERLAY_BUILD" >/dev/null
fi
if [[ "$ACTC_USE_IMPORT_OVERLAY" != "0" ]]; then
  bash "$ACTC_IMPORT_OVERLAY_BUILD" >/dev/null
fi
if [[ "$ACTC_USE_EMIT_OVERLAY" != "0" ]]; then
  bash "$ACTC_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_LOCAL_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_REAL_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_REAL_CONTROL_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_REAL_WHILE_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_RUNTIME_CONDITION_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_RUNTIME_SEQUENCE_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_RUNTIME_NESTED_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_LOCAL_RUNTIME_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_LOCAL_MIXED_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_FIXED_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_REAL_FUNCTION_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_REAL_POSTFIX_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_REAL_POSTFIX_CONTROL_EMIT_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_NATIVE_REAL_POSTFIX_MULTI_CONTROL_EMIT_OVERLAY_BUILD" >/dev/null
fi
if [[ "$ACTC_USE_BODY_OVERLAY" != "0" ]]; then
  ACTC_KEEP_BODY_RESIDENT_FALLBACK="$ACTC_KEEP_BODY_RESIDENT_FALLBACK" bash "$ACTC_BODY_OVERLAY_BUILD" >/dev/null
  bash "$ACTC_PREALLOC_OVERLAY_BUILD" >/dev/null
fi
printf '%s\n' "$PRG"
