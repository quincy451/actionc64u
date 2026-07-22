#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

./tools/env_check.sh
python3 -m pytest -q
python3 ./tools/build_release_image.py

if command -v x64sc >/dev/null 2>&1; then
  (cd "$ROOT_DIR/../udos" && make vice-release)
else
  echo "Skipping VICE verification: x64sc not found on PATH"
fi

echo "Smoke pass completed."
