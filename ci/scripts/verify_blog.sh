#!/usr/bin/env bash
set -euo pipefail

PUBLIC_DIR="${1:-public-blog}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

echo "[verify-blog] target=${PUBLIC_DIR}"

if [[ ! -d "${PUBLIC_DIR}" ]]; then
  echo "[verify-blog] ERROR: directory not found: ${PUBLIC_DIR}" >&2
  exit 1
fi

required=(
  "index.html"
  "ja/index.html"
  "en/index.html"
  "posts/index.html"
  "posts/index.xml"
  "archive/index.html"
  "en/archive/index.html"
  "feeds/atom.xml"
  "sitemap.xml"
  "robots.txt"
  "images/site-sprite.svg"
  "fonts/subsets/noto-sans-jp-500.ja.woff2"
  "fonts/subsets/noto-sans-jp-500.en.woff2"
)

for f in "${required[@]}"; do
  if [[ ! -f "${PUBLIC_DIR}/${f}" ]]; then
    echo "[verify-blog] ERROR: missing required output: ${PUBLIC_DIR}/${f}" >&2
    exit 1
  fi
done

for label in "All posts" "Archive" "Subscribe"; do
  if ! rg -q "${label}" "${PUBLIC_DIR}/en/index.html"; then
    echo "[verify-blog] ERROR: English blog navigation is missing: ${label}" >&2
    exit 1
  fi
done

for symbol in icon-bi-file-earmark-richtext icon-bi-archive icon-bi-rss icon-bi-box-arrow-up-right; do
  if ! rg -q "id=.?${symbol}\\b" "${PUBLIC_DIR}/en/index.html"; then
    echo "[verify-blog] ERROR: blog page sprite is missing: ${symbol}" >&2
    exit 1
  fi
done

if ! rg -q 'href=/en/feeds/atom.xml[^>]*target=_blank[^>]*rel="noopener alternate"' "${PUBLIC_DIR}/en/index.html"; then
  echo "[verify-blog] ERROR: Subscribe must open the localized feed in a new tab" >&2
  exit 1
fi

if [[ ! -f "${PUBLIC_DIR}/CNAME" ]] || [[ "$(tr -d '\r\n' < "${PUBLIC_DIR}/CNAME")" != "blog.ray34g.com" ]]; then
  echo "[verify-blog] ERROR: standalone blog output must contain CNAME=blog.ray34g.com" >&2
  exit 1
fi

"${ROOT_DIR}/ci/scripts/verify_robots.sh" \
  "${PUBLIC_DIR}/robots.txt" \
  "https://blog.ray34g.com/sitemap.xml"

if ! rg -q 'data-back-to-top' "${PUBLIC_DIR}/index.html"; then
  echo "[verify-blog] ERROR: blog home is missing the contextual back-to-top action" >&2
  exit 1
fi

if ! rg -q 'data-back-to-top' "${PUBLIC_DIR}/posts/index.html"; then
  echo "[verify-blog] ERROR: posts index is missing the contextual back-to-top action" >&2
  exit 1
fi

python3 - "${PUBLIC_DIR}/feeds/atom.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

feed_path = Path(sys.argv[1])
root = ET.parse(feed_path).getroot()
namespace = {"atom": "http://www.w3.org/2005/Atom"}

if root.tag != "{http://www.w3.org/2005/Atom}feed":
    raise SystemExit(f"[verify-blog] ERROR: unexpected Atom root element: {root.tag}")

self_links = root.findall("atom:link[@rel='self']", namespace)
expected_self = "https://blog.ray34g.com/feeds/atom.xml"
if len(self_links) != 1 or self_links[0].get("href") != expected_self:
    raise SystemExit("[verify-blog] ERROR: Atom self link is missing or incorrect")

entries = root.findall("atom:entry", namespace)
if not entries:
    raise SystemExit("[verify-blog] ERROR: Atom feed contains no blog entries")

for entry in entries:
    link = entry.find("atom:link[@rel='alternate']", namespace)
    href = link.get("href", "") if link is not None else ""
    if not href.startswith("https://blog.ray34g.com/posts/"):
        raise SystemExit(f"[verify-blog] ERROR: unexpected Atom entry URL: {href}")
PY

if ! find "${PUBLIC_DIR}/posts" -mindepth 2 -type f -name 'index.html' | rg -q .; then
  echo "[verify-blog] ERROR: expected at least one rendered post detail page" >&2
  exit 1
fi

if [[ -e "${PUBLIC_DIR}/notes" ]]; then
  echo "[verify-blog] ERROR: retired notes section was generated" >&2
  exit 1
fi

if [[ -f "${PUBLIC_DIR}/fonts/subsets/manifest.json" ]]; then
  echo "[verify-blog] ERROR: font subset manifest should not be published" >&2
  exit 1
fi

if [[ -d "${PUBLIC_DIR}/fonts/subsets/dictionaries" ]]; then
  echo "[verify-blog] ERROR: font subset dictionaries should not be published" >&2
  exit 1
fi

if find "${PUBLIC_DIR}" -type l | rg -q .; then
  echo "[verify-blog] ERROR: unexpected symlinks in build output" >&2
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
      echo "[verify-blog] MISSING REF in ${file#"${PUBLIC_DIR}"/}: ${ref} -> ${target#"${PUBLIC_DIR}"/}"
      missing_refs=1
    fi
  done < <(rg -No '(?:href|src)="([^"]+)"' "${file}" --replace '$1' || true)
done < <(find "${PUBLIC_DIR}" -type f -name '*.html' ! -path "${PUBLIC_DIR}/reports/*" | sort)

if [[ "${missing_refs}" -ne 0 ]]; then
  echo "[verify-blog] ERROR: missing local references detected" >&2
  exit 1
fi

"${ROOT_DIR}/ci/scripts/check_i18n_keys.sh"

echo "[verify-blog] done"
