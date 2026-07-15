#!/usr/bin/env bash
set -euo pipefail

PUBLIC_DIR="${1:-public}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

echo "[verify] target=${PUBLIC_DIR}"

if [[ ! -d "${PUBLIC_DIR}" ]]; then
  echo "[verify] ERROR: directory not found: ${PUBLIC_DIR}" >&2
  exit 1
fi

if [[ -f "${PUBLIC_DIR}/CNAME" ]]; then
  echo "[verify] ERROR: CNAME belongs to the portal artifact repository, not shared source output" >&2
  exit 1
fi

required=(
  "index.html"
  "ja/index.html"
  "en/index.html"
  "sitemap.xml"
  "robots.txt"
  "images/site-sprite.svg"
  "fonts/subsets/noto-sans-jp-500.ja.woff2"
  "fonts/subsets/noto-sans-jp-500.en.woff2"
)

for f in "${required[@]}"; do
  if [[ ! -f "${PUBLIC_DIR}/${f}" ]]; then
    echo "[verify] ERROR: missing required output: ${PUBLIC_DIR}/${f}" >&2
    exit 1
  fi
done

echo "[verify] required pages check passed"

"${ROOT_DIR}/ci/scripts/verify_robots.sh" \
  "${PUBLIC_DIR}/robots.txt" \
  "https://www.ray34g.com/sitemap.xml"

if rg -q 'data-back-to-top' "${PUBLIC_DIR}/index.html"; then
  echo "[verify] ERROR: portal home should not render the contextual back-to-top action" >&2
  exit 1
fi

if [[ -e "${PUBLIC_DIR}/posts" ]]; then
  echo "[verify] ERROR: portal build must link to the blog instead of publishing posts" >&2
  exit 1
fi

for symbol in icon-custom-chevron-right icon-fab-github; do
  if ! rg -q "id=.?${symbol}\\b" "${PUBLIC_DIR}/images/site-sprite.svg"; then
    echo "[verify] ERROR: missing required site sprite symbol: ${symbol}" >&2
    exit 1
  fi
done

echo "[verify] required site sprite symbols check passed"

if [[ -f "${PUBLIC_DIR}/fonts/subsets/manifest.json" ]]; then
  echo "[verify] ERROR: font subset manifest should not be published" >&2
  exit 1
fi

if [[ -d "${PUBLIC_DIR}/fonts/subsets/dictionaries" ]]; then
  echo "[verify] ERROR: font subset dictionaries should not be published" >&2
  exit 1
fi

if find "${PUBLIC_DIR}" -type l | rg -q .; then
  echo "[verify] ERROR: unexpected symlinks in build output" >&2
  exit 1
fi

missing_refs=0
while IFS= read -r file; do
  while IFS= read -r ref; do
    path="${ref%%[?#]*}"
    [[ -z "${path}" ]] && continue
    [[ "${path}" == "/" ]] && continue
    [[ "${path}" == http://* || "${path}" == https://* || "${path}" == mailto:* || "${path}" == tel:* || "${path}" == data:* || "${path}" == javascript:* || "${path}" == \#* ]] && continue

    if [[ "${path}" == /* ]]; then
      target="${PUBLIC_DIR}${path}"
    else
      target="$(dirname "${file}")/${path}"
    fi

    if [[ ! -e "${target}" ]]; then
      echo "[verify] MISSING REF in ${file#"${PUBLIC_DIR}"/}: ${ref} -> ${target#"${PUBLIC_DIR}"/}"
      missing_refs=1
    fi
  done < <(rg -No '(?:href|src)="([^"]+)"' "${file}" --replace '$1' || true)
done < <(find "${PUBLIC_DIR}" -type f -name '*.html' ! -path "${PUBLIC_DIR}/reports/*" | sort)

if [[ "${missing_refs}" -ne 0 ]]; then
  echo "[verify] ERROR: missing local references detected" >&2
  exit 1
fi

echo "[verify] local reference check passed"

"${ROOT_DIR}/ci/scripts/check_i18n_keys.sh"

echo "[verify] done"
