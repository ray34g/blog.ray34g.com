#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-public-example-menu}"
HUGO_ENV="${HUGO_ENVIRONMENT:-menu-test}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/exampleSite"
TMP_BUILD_DIR=""
TMP_CACHE_DIR=""

cleanup() {
  [[ -n "${TMP_BUILD_DIR}" ]] && rm -rf "${TMP_BUILD_DIR}"
  [[ -n "${TMP_CACHE_DIR}" ]] && rm -rf "${TMP_CACHE_DIR}"
}
trap cleanup EXIT HUP INT TERM

echo "[example] environment=${HUGO_ENV} output=${OUT_DIR}"

if ! command -v hugo >/dev/null 2>&1; then
  echo "[example] ERROR: hugo command not found" >&2
  exit 1
fi

cd "${ROOT_DIR}"

ensure_node_modules() {
  if [[ -d "${ROOT_DIR}/node_modules" ]]; then
    return 0
  fi

  if [[ ! -f "${ROOT_DIR}/package-lock.json" ]]; then
    echo "[example] ERROR: package-lock.json is required; refusing npm install without a lockfile" >&2
    exit 1
  fi

  local npm_cache="${NPM_CONFIG_CACHE:-/opt/npm-cache}"
  local npm_ci_offline="${NPM_CI_OFFLINE:-auto}"
  local -a npm_args=(ci --ignore-scripts --no-audit --no-fund)

  case "${npm_ci_offline}" in
    1|true|yes|on)
      npm "${npm_args[@]}" --offline --cache "${npm_cache}"
      ;;
    0|false|no|off)
      npm "${npm_args[@]}"
      ;;
    auto)
      if [[ -n "${CI:-}" ]]; then
        npm "${npm_args[@]}" --offline --cache "${npm_cache}"
      else
        npm "${npm_args[@]}"
      fi
      ;;
    *)
      echo "[example] ERROR: invalid NPM_CI_OFFLINE value: ${npm_ci_offline}" >&2
      exit 1
      ;;
  esac
}

ensure_node_modules

npm run icons:sync

TMP_BUILD_DIR="$(mktemp -d)"
TMP_CACHE_DIR="$(mktemp -d)"
mkdir -p "${SOURCE_DIR}/data"

echo "[example] first pass for site sprite usage"
rm -f "${SOURCE_DIR}/data/site_sprite_usage.json"
hugo \
  --source "${SOURCE_DIR}" \
  --environment "${HUGO_ENV}" \
  --gc \
  --minify \
  --cleanDestinationDir \
  --destination "${TMP_BUILD_DIR}" \
  --cacheDir "${TMP_CACHE_DIR}"

echo "[example] analyze site sprite usage"
python3 ci/scripts/tools/analyze_site_sprite_usage.py \
  --input-dir "${TMP_BUILD_DIR}" \
  --output "${SOURCE_DIR}/data/site_sprite_usage.json"

echo "[example] final pass"
hugo \
  --source "${SOURCE_DIR}" \
  --environment "${HUGO_ENV}" \
  --gc \
  --minify \
  --cleanDestinationDir \
  --destination "${ROOT_DIR}/${OUT_DIR}" \
  --cacheDir "${TMP_CACHE_DIR}"

echo "[example] done"
