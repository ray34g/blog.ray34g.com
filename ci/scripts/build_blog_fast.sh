#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-public-blog}"
HUGO_ENV="${HUGO_ENVIRONMENT:-production-blog}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

echo "[build-blog-fast] environment=${HUGO_ENV} output=${OUT_DIR}"

if [[ ! -d node_modules ]]; then
  echo "[build-blog-fast] ERROR: node_modules is missing; run npm ci first" >&2
  exit 1
fi

# Reuse reviewed, committed font subsets and analysis output. A full build in
# the PR quality lane refreshes these assets when theme or content coverage
# changes.
npm run icons:sync
hugo --gc --minify --cleanDestinationDir \
  --environment "${HUGO_ENV}" \
  --destination "${OUT_DIR}"

echo "[build-blog-fast] done"
