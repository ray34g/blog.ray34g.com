#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${RENDER_REPORT_DIR:-$ROOT_DIR/static/reports/visual-diff-current}"

cd "$ROOT_DIR"
rm -rf "$REPORT_DIR"
npm run build:pages
npm run build:preview
npm run render-report
