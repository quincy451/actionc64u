#!/usr/bin/env bash
set -euo pipefail

RUN=0

usage() {
  cat <<'USAGE'
Usage: ./tools/setup_wsl.sh [--print|--run]

Default behavior prints the recommended install commands.
Use --run only when you intentionally invoke the script under sudo/root.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --print)
      RUN=0
      ;;
    --run)
      RUN=1
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

APT_PACKAGES=(
  git
  make
  python3
  python3-pip
  build-essential
  clang
  cmake
  poppler-utils
  cpmtools
  default-jre-headless
  vice
  expect
  socat
  netcat-openbsd
  libfmt-dev
  fp-compiler
  moreutils
  mame
  srecord
  64tass
  libreadline-dev
)

print_plan() {
  echo "Suggested WSL2 packages for ActionC64U and local CP/M-65 work:"
  echo
  echo "  apt-get update"
  printf '  apt-get install -y'
  local package
  for package in "${APT_PACKAGES[@]}"; do
    printf ' %s' "$package"
  done
  printf '\n'
  echo
  echo "Install llvm-mos separately; cpm65-u64 expects its bin directory as LLVM=<path>/ (default in its Makefile is /opt/pkg/llvm-mos/bin)."
  echo "If your distro packages cc1541, install it too; otherwise build it separately and place it on PATH."
  echo "Optional full pytest install: python3 -m pip install --user pytest"
}

if (( RUN == 0 )); then
  print_plan
  echo
  echo "Re-run with: sudo ./tools/setup_wsl.sh --run"
  exit 0
fi

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "--run requires root. Re-run with: sudo ./tools/setup_wsl.sh --run" >&2
  exit 1
fi

print_plan
apt-get update
apt-get install -y "${APT_PACKAGES[@]}"
echo "Skipping llvm-mos and pytest automatic installation; follow the printed guidance for those."
