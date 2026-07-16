#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT="${LINK_CHECK_PORT:-1313}"
URL="http://localhost:${PORT}/"
LOG_FILE="$(mktemp)"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  rm -f "${LOG_FILE}"
}
trap cleanup EXIT HUP INT TERM

cd "${ROOT_DIR}"

hugo server \
  --environment production-blog \
  --minify \
  --disableLiveReload \
  --baseURL="${URL}" \
  --bind=127.0.0.1 \
  --port="${PORT}" \
  --renderToMemory \
  --noTimes >"${LOG_FILE}" 2>&1 &
SERVER_PID=$!

if ! curl -fsS --retry 30 --retry-connrefused --retry-delay 1 "${URL}" >/dev/null; then
  cat "${LOG_FILE}" >&2
  exit 1
fi

linkinator "${URL}" \
  --recurse \
  --skip "^https?://(?!localhost:${PORT})"
