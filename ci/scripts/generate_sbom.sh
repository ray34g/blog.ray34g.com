#!/usr/bin/env sh
set -eu

ROOT_DIR="${CI_PROJECT_DIR:-$(unset CDPATH && cd -- "$(dirname -- "$0")/../.." && pwd)}"
OUTPUT_DIR="${SBOM_OUTPUT_DIR:-$ROOT_DIR/ci/sbom}"

cd "$ROOT_DIR"

if [ ! -f package-lock.json ]; then
  echo "generate_sbom: package-lock.json is required" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

if command -v trivy >/dev/null 2>&1; then
  trivy fs \
    --skip-version-check \
    --format spdx-json \
    --output "$OUTPUT_DIR/npm.spdx.json" \
    --pkg-types library \
    --include-dev-deps \
    --skip-dirs "$ROOT_DIR/themes" \
    "$ROOT_DIR"
else
  npm sbom --sbom-format spdx > "$OUTPUT_DIR/npm.spdx.json"
fi

echo "generate_sbom: wrote $OUTPUT_DIR/npm.spdx.json"
