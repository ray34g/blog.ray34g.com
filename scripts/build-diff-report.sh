#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_BUILD_DIR="${REPORT_BASE_BUILD_DIR:-$ROOT_DIR/.report-build/baseline}"
CAND_BUILD_DIR="${REPORT_CAND_BUILD_DIR:-$ROOT_DIR/.report-build/candidate}"
MAIN_REF="${REPORT_BASE_REF:-origin/main}"
HUGO_ENV="${HUGO_ENVIRONMENT:-production}"

if ! command -v hugo >/dev/null 2>&1; then
  echo "[diff-report] ERROR: hugo not found in PATH" >&2
  exit 1
fi

rm -rf "$BASE_BUILD_DIR" "$CAND_BUILD_DIR"
mkdir -p "$BASE_BUILD_DIR" "$CAND_BUILD_DIR"

"$ROOT_DIR/ci/scripts/build_pages.sh" "$CAND_BUILD_DIR"

tmp_wt="$ROOT_DIR/.report-build/.wt-main"
rm -rf "$tmp_wt"
git -C "$ROOT_DIR" worktree add --detach "$tmp_wt" "$MAIN_REF" >/dev/null
trap 'git -C "$ROOT_DIR" worktree remove --force "$tmp_wt" >/dev/null 2>&1 || true' EXIT

(
  cd "$tmp_wt"
  hugo --gc --minify --cleanDestinationDir --environment "$HUGO_ENV" --destination "$BASE_BUILD_DIR"
)

cd "$ROOT_DIR"
node scripts/render-report.mjs

echo "[diff-report] done: public/reports/diff-report/index.html"
