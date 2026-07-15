#!/usr/bin/env bash
set -euo pipefail

ROBOTS_FILE="${1:?usage: verify_robots.sh ROBOTS_FILE SITEMAP_URL}"
SITEMAP_URL="${2:?usage: verify_robots.sh ROBOTS_FILE SITEMAP_URL}"

required_lines=(
  "User-agent: *"
  "Disallow: /admin/"
  "User-agent: OAI-SearchBot"
  "User-agent: Claude-SearchBot"
  "User-agent: GPTBot"
  "User-agent: ClaudeBot"
  "User-agent: Google-Extended"
  "Sitemap: ${SITEMAP_URL}"
)

for line in "${required_lines[@]}"; do
  if ! rg -Fqx "${line}" "${ROBOTS_FILE}"; then
    echo "[verify-robots] ERROR: missing expected directive: ${line}" >&2
    exit 1
  fi
done

for agent in GPTBot ClaudeBot Google-Extended; do
  if ! awk -v agent="${agent}" '
    $0 == "User-agent: " agent { active = 1; next }
    active && /^User-agent:/ { exit 1 }
    active && $0 == "Disallow: /" { found = 1; exit 0 }
    END { exit(found ? 0 : 1) }
  ' "${ROBOTS_FILE}"; then
    echo "[verify-robots] ERROR: ${agent} is not fully disallowed" >&2
    exit 1
  fi
done

echo "[verify-robots] policy check passed"
