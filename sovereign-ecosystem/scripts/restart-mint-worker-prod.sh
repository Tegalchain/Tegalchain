#!/usr/bin/env bash
# Restart mint worker with Phase 7 prod/staging profile (Bearer + tegalid).
# Usage:
#   export MINT_WORKER_BEARER_TOKEN=<secret>
#   ./scripts/restart-mint-worker-prod.sh
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
fi

exec ./scripts/start-mint-worker-prod.sh
