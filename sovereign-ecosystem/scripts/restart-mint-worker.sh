#!/usr/bin/env bash
# Stop the mint worker on :8090 and start a fresh process (pick up code after git pull).
# Usage: ./scripts/restart-mint-worker.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if curl -sf http://127.0.0.1:8090/health >/dev/null 2>&1; then
  echo "==> Stopping mint worker on :8090"
  pkill -f '[p]ython.*integrations\.mint_worker' 2>/dev/null || \
    pkill -f '[p]ython3.*integrations\.mint_worker' 2>/dev/null || \
    pkill -f 'integrations\.mint_worker' 2>/dev/null || true
  for _ in $(seq 1 20); do
    if ! curl -sf http://127.0.0.1:8090/health >/dev/null 2>&1; then
      break
    fi
    sleep 0.25
  done
  if curl -sf http://127.0.0.1:8090/health >/dev/null 2>&1; then
    echo "ERROR: mint worker still listening on :8090 — stop it manually (Ctrl+C in its shell)" >&2
    exit 1
  fi
fi

exec ./scripts/start-mint-worker.sh
