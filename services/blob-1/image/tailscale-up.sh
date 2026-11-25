#!/usr/bin/env bash
set -Eeuo pipefail

for _ in {1..60}; do
  if tailscale status --json >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [[ "$(tailscale status --json 2>/dev/null | jq -r '.BackendState // empty')" == "Running" ]]; then
  exit 0
fi

if [[ -z "${TAILSCALE_AUTH_KEY:-}" ]]; then
  printf '[blob-1-tailscale] TAILSCALE_AUTH_KEY not set; skipping tailscale up\n'
  exit 0
fi

exec tailscale up \
  --auth-key="${TAILSCALE_AUTH_KEY}" \
  --hostname="${TAILSCALE_HOSTNAME:-blob-1}" \
  --accept-dns=false
