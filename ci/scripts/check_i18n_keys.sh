#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v rg >/dev/null 2>&1; then
  echo "[i18n] ERROR: rg command is required" >&2
  exit 1
fi

if [[ ! -d data || ! -d i18n ]]; then
  echo "[i18n] no data/i18n directories found; skipping key check"
  exit 0
fi

keys_file="$(mktemp)"
missing=0

rg -No --replace '$1' -e 'i18n_key\s*=\s*"([^"]+)"' data | sed 's#^[^:]*:##' | sort -u > "${keys_file}" || true

if [[ ! -s "${keys_file}" ]]; then
  echo "[i18n] no i18n_key references found in data/*.toml"
  rm -f "${keys_file}"
  exit 0
fi

echo "[i18n] validating keys from data/ against i18n/*.toml"
while IFS= read -r key; do
  for lang in ja en; do
    if [[ ! -f "i18n/${lang}.toml" ]] || ! rg -q "^\[${key}\]$" "i18n/${lang}.toml"; then
      echo "[i18n] MISSING: key='${key}' lang='${lang}'"
      missing=1
    fi
  done
done < "${keys_file}"

rm -f "${keys_file}"

if [[ "${missing}" -ne 0 ]]; then
  echo "[i18n] failed"
  exit 1
fi

echo "[i18n] passed"
