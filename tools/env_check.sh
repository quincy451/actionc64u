#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STRICT=0

usage() {
  cat <<'USAGE'
Usage: ./tools/env_check.sh [--strict]

Advisory environment check for ActionC64U.
  --strict   exit non-zero when any required dependency is missing
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict)
      STRICT=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

required_missing=0
optional_missing=0

print_header() {
  printf '%-8s %-8s %-24s %s\n' "STATUS" "REQUIRED" "CHECK" "DETAIL"
  printf '%-8s %-8s %-24s %s\n' "------" "--------" "-----" "------"
}

record_result() {
  local required_flag="$1"
  local label="$2"
  local status="$3"
  local detail="$4"

  printf '%-8s %-8s %-24s %s\n' "$status" "$required_flag" "$label" "$detail"

  if [[ "$status" == "FAIL" ]]; then
    if [[ "$required_flag" == "yes" ]]; then
      required_missing=$((required_missing + 1))
    else
      optional_missing=$((optional_missing + 1))
    fi
  fi
}

command_path() {
  command -v "$1" 2>/dev/null || true
}

check_command() {
  local label="$1"
  local required_flag="$2"
  local command_name="$3"
  local install_hint="$4"
  local path
  path="$(command_path "$command_name")"

  if [[ -n "$path" ]]; then
    record_result "$required_flag" "$label" "PASS" "$path"
  else
    record_result "$required_flag" "$label" "FAIL" "$install_hint"
  fi
}

check_any_command() {
  local label="$1"
  local required_flag="$2"
  local install_hint="$3"
  shift 3

  local found=()
  local name path
  for name in "$@"; do
    path="$(command_path "$name")"
    if [[ -n "$path" ]]; then
      found+=("$name=$path")
    fi
  done

  if [[ ${#found[@]} -gt 0 ]]; then
    record_result "$required_flag" "$label" "PASS" "${found[*]}"
  else
    record_result "$required_flag" "$label" "FAIL" "$install_hint"
  fi
}

check_all_commands() {
  local label="$1"
  local required_flag="$2"
  local install_hint="$3"
  shift 3

  local found=()
  local missing=()
  local name path
  for name in "$@"; do
    path="$(command_path "$name")"
    if [[ -n "$path" ]]; then
      found+=("$name=$path")
    else
      missing+=("$name")
    fi
  done

  if [[ ${#missing[@]} -eq 0 ]]; then
    record_result "$required_flag" "$label" "PASS" "${found[*]}"
  else
    record_result "$required_flag" "$label" "FAIL" "$install_hint (missing: ${missing[*]})"
  fi
}

check_pytest() {
  local metadata_output
  if metadata_output="$(python3 - <<'PY' 2>/dev/null
from importlib import metadata
print(metadata.version('pytest'))
PY
)"; then
    record_result "yes" "pytest" "PASS" "installed package version ${metadata_output}"
    return
  fi

  local shim_output
  if shim_output="$(cd "$ROOT_DIR" && python3 -m pytest --version 2>/dev/null)"; then
    record_result "yes" "pytest" "PASS" "repo-local fallback available (${shim_output}); install with: python3 -m pip install --user pytest for a non-shim environment"
    return
  fi

  record_result "yes" "pytest" "FAIL" "install with: python3 -m pip install --user pytest"
}

print_header
check_command "git" "yes" "git" "install package: git"
check_command "make" "yes" "make" "install package: make"
check_command "python3" "yes" "python3" "install package: python3"
check_command "pip3" "yes" "pip3" "install package: python3-pip"
check_any_command "C compiler" "yes" "install build-essential or clang" gcc clang
check_any_command "C++ compiler" "yes" "install build-essential or clang" g++ clang++
check_command "cmake" "no" "cmake" "install package: cmake"
check_pytest
check_command "pdftotext" "no" "pdftotext" "install package: poppler-utils"
check_all_commands "cpmtools" "no" "install package: cpmtools" cpmcp cpmls cpmrm
check_command "cc1541" "no" "cc1541" "install distro package if available, otherwise build and add to PATH"
check_command "java" "no" "java" "install package: default-jre-headless"
check_any_command "VICE" "no" "install package: vice (needs x64sc for later C64 validation)" x64sc vice
check_any_command "automation helper" "no" "install one of: expect, socat, netcat-openbsd" expect socat nc

printf '\nSummary: %d required missing, %d optional missing.\n' "$required_missing" "$optional_missing"
if (( required_missing > 0 )); then
  echo "Required dependencies are missing. Run ./tools/setup_wsl.sh for install guidance."
fi
if (( optional_missing > 0 )); then
  echo "Optional dependencies are missing. These are not blocking bootstrap, but later prompts may need them."
fi

if (( STRICT == 1 && required_missing > 0 )); then
  exit 1
fi
