#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF_PATH="$ROOT_DIR/docs/inspiration/action.pdf"
TXT_PATH="$ROOT_DIR/docs/inspiration/action_manual.txt"

if ! command -v pdftotext >/dev/null 2>&1; then
  echo "pdftotext is not installed."
  echo "Install it with: sudo apt-get update && sudo apt-get install -y poppler-utils"
  exit 1
fi

if [[ ! -f "$PDF_PATH" ]]; then
  echo "Missing input PDF: $PDF_PATH"
  exit 1
fi

pdftotext "$PDF_PATH" "$TXT_PATH"
echo "Extracted manual text to: $TXT_PATH"
