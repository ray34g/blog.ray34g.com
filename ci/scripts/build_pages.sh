#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-public}"
HUGO_ENV="${HUGO_ENVIRONMENT:-production}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_BUILD_DIR=""
TMP_CACHE_DIR=""

cleanup() {
  [[ -n "${TMP_BUILD_DIR}" ]] && rm -rf "${TMP_BUILD_DIR}"
  [[ -n "${TMP_CACHE_DIR}" ]] && rm -rf "${TMP_CACHE_DIR}"
}
trap cleanup EXIT HUP INT TERM

echo "[build] environment=${HUGO_ENV} output=${OUT_DIR}"

if ! command -v hugo >/dev/null 2>&1; then
  echo "[build] ERROR: hugo command not found" >&2
  exit 1
fi

cd "${ROOT_DIR}"

ensure_node_modules() {
  if [[ -d "${ROOT_DIR}/node_modules" ]]; then
    return 0
  fi

  if [[ ! -f "${ROOT_DIR}/package-lock.json" ]]; then
    echo "[build] ERROR: package-lock.json is required; refusing npm install without a lockfile" >&2
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
      echo "[build] ERROR: invalid NPM_CI_OFFLINE value: ${npm_ci_offline}" >&2
      exit 1
      ;;
  esac
}

ensure_node_modules

npm run icons:sync

TMP_BUILD_DIR="$(mktemp -d)"
TMP_CACHE_DIR="$(mktemp -d)"

echo "[build] first pass for generated asset analysis"
rm -f data/font_weight_usage.json data/site_sprite_usage.json
hugo --gc --minify --cleanDestinationDir --environment "${HUGO_ENV}" --destination "${TMP_BUILD_DIR}" --cacheDir "${TMP_CACHE_DIR}"

echo "[build] analyze site sprite usage"
python3 ci/scripts/tools/analyze_site_sprite_usage.py \
  --input-dir "${TMP_BUILD_DIR}" \
  --output data/site_sprite_usage.json

echo "[build] analyze font weight usage"
python3 ci/scripts/tools/analyze_bootstrap_weights.py \
  --input-dir "${TMP_BUILD_DIR}" \
  --output data/font_weight_usage.json

if [[ "${ENABLE_FONT_SUBSET:-1}" == "1" ]]; then
  echo "[build] build font subsets"
  "${ROOT_DIR}/scripts/build-font-subsets.sh" "${TMP_BUILD_DIR}"
fi

echo "[build] final pass"
hugo --gc --minify --cleanDestinationDir --environment "${HUGO_ENV}" --destination "${OUT_DIR}"

echo "[build] done"
