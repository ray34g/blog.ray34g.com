#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-public-blog}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"
HUGO_ENVIRONMENT="${HUGO_ENVIRONMENT:-production-blog}" ./ci/scripts/build_pages.sh "${OUT_DIR}"
