#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC_DIR="${1:-$ROOT_DIR/public}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[font-subset] ERROR: python3 not found" >&2
  exit 1
fi

if ! command -v pyftsubset >/dev/null 2>&1; then
  if [[ "${REQUIRE_FONT_SUBSET:-0}" == "1" ]]; then
    echo "[font-subset] ERROR: pyftsubset was not found in PATH." >&2
    echo "[font-subset] Install with: python3 -m pip install -r requirements-dev.txt" >&2
    exit 1
  fi
  echo "[font-subset] SKIP: pyftsubset was not found in PATH."
  echo "[font-subset] Install with: python3 -m pip install -r requirements-dev.txt"
  exit 0
fi

if [[ ! -d "$PUBLIC_DIR" ]]; then
  echo "[font-subset] ERROR: missing public dir: $PUBLIC_DIR" >&2
  exit 1
fi

if [[ ! -d "$ROOT_DIR/assets/fonts/source" ]]; then
  echo "[font-subset] SKIP: assets/fonts/source is missing."
  echo "[font-subset] Place source fonts under: assets/fonts/source/{poppins,noto-sans-jp,line-seed-jp}"
  exit 0
fi

python3 "$ROOT_DIR/scripts/build-font-subsets.py" \
  --input-dir "$PUBLIC_DIR" \
  --output-dir "$ROOT_DIR/assets/fonts/subsets" \
  --manifest "$ROOT_DIR/assets/fonts/subsets/manifest.json" \
  --families poppins noto line-seed \
  --languages ja en \
  --exclude-emoji

echo "[font-subset] done"
