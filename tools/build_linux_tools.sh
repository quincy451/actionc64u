#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/linux_tools"
SRC="$ROOT_DIR/src/tools_linux/action_workspace_tools.cpp"
BIN="$BUILD_DIR/action-workspace-tools"
CXX="${CXX:-g++}"
SQLITE_CFLAGS="$(pkg-config --cflags sqlite3)"
SQLITE_LIBS="$(pkg-config --libs sqlite3)"

mkdir -p "$BUILD_DIR"

if [[ ! -x "$BIN" || "$SRC" -nt "$BIN" ]]; then
    # shellcheck disable=SC2086
    "$CXX" -std=c++17 -Wall -Wextra -Werror -O0 $SQLITE_CFLAGS "$SRC" -o "$BIN" $SQLITE_LIBS
fi

for tool in actnew actadd actwork actsrc actfile actchk actdir actcopy actdel actmkdir actrmdir actmove actren actwrite actinfo actmon actdbg acttree tree xcopy deltree actedit act2save actsave actc alink; do
    ln -sf action-workspace-tools "$BUILD_DIR/$tool"
done

echo "$BUILD_DIR"
