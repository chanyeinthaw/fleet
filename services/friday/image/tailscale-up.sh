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

: "${TAILSCALE_AUTH_KEY:?TAILSCALE_AUTH_KEY is required until this node is registered}"

exec tailscale up \
  --auth-key="${TAILSCALE_AUTH_KEY}" \
  --hostname="${TAILSCALE_HOSTNAME:-friday}" \
  --accept-dns=false
