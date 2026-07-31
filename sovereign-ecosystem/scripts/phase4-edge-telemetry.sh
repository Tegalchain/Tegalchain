#!/usr/bin/env bash
# Phase 4 — edge producer → mint worker → mock drain (lab).
#
# Usage:
#   ./scripts/phase4-edge-telemetry.sh zeegate    # Python Zeegate sim → POST
#   ./scripts/phase4-edge-telemetry.sh bytenergy  # Bytenergy client → POST
#   ./scripts/phase4-edge-telemetry.sh both       # both producers, then drain
#   ./scripts/phase4-edge-telemetry.sh drain      # mock drain only
#   ./scripts/phase4-edge-telemetry.sh verify     # queue stats + health
#
# Prerequisites: mint worker on :8090 (./scripts/start-mint-worker.sh)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
export MINT_WORKER_URL="$MINT_URL"
export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export TEGALCHAIN_OUTBOX_DIR="${TEGALCHAIN_OUTBOX_DIR:-$ROOT/tegalchain/data/outbox}"
export TEGALCHAIN_IDENTITY_MODE="${TEGALCHAIN_IDENTITY_MODE:-dev}"

require_worker() {
  if ! curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
    echo "ERROR: mint worker not reachable at ${MINT_URL}" >&2
    echo "  Start: ./scripts/start-mint-worker.sh  (leave that shell open)" >&2
    exit 1
  fi
}

post_zeegate() {
  echo "==> Zeegate Python sim → ${MINT_URL}"
  GREETELEMETRY_FORMAT="${GREETELEMETRY_FORMAT:-legacy}" "$PY" integrations/zeegate_telemetry/client.py
}

post_bytenergy() {
  echo "==> Bytenergy client → ${MINT_URL}"
  "$PY" bytenergy-utility/client.py
}

drain_queue() {
  echo "==> Mock drain"
  bash ./scripts/replit-mint-drain.sh "${1:-10}"
}

verify_lab() {
  echo "==> Mint worker health"
  curl -sf "${MINT_URL}/health" | "$PY" -m json.tool
  echo "==> Queue stats"
  curl -sf "${MINT_URL}/v1/queue/stats" | "$PY" -m json.tool
  echo
  echo "Verify a record (use gtr_id from POST response above):"
  echo "  curl -s \"${MINT_URL}/v1/telemetry/records/{gtr_id}\" | $PY -m json.tool"
}

MODE="${1:-both}"

case "$MODE" in
  zeegate)
    require_worker
    post_zeegate
    ;;
  bytenergy)
    require_worker
    post_bytenergy
    ;;
  both)
    require_worker
    post_zeegate
    post_bytenergy
    drain_queue 10
    verify_lab
    ;;
  drain)
    drain_queue "${2:-10}"
    verify_lab
    ;;
  verify)
    require_worker
    verify_lab
    ;;
  *)
    echo "Usage: $0 [zeegate|bytenergy|both|drain|verify]" >&2
    exit 2
    ;;
esac
