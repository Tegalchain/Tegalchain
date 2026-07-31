#!/usr/bin/env bash
# Phase 5 — ingest (optional) + Cosmos REST drain + verify hints.
#
# Prerequisites (three shells on Replit/WSL):
#   1. ./scripts/start-mint-worker.sh
#   2. ./scripts/start-cosmos-anchor-lab.sh
#   3. this script
#
# Usage:
#   ./scripts/phase5-cosmos-drain.sh              # drain pending queue via cosmos
#   ./scripts/phase5-cosmos-drain.sh ingest       # POST one Zeegate row, then drain
#   ./scripts/phase5-cosmos-drain.sh verify <gtr_id>
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
COSMOS_URL="${TEGALCHAIN_COSMOS_REST_URL:-http://127.0.0.1:1317}"
export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export TEGALCHAIN_OUTBOX_DIR="${TEGALCHAIN_OUTBOX_DIR:-$ROOT/tegalchain/data/outbox}"
export TEGALCHAIN_SUBMITTER_BACKEND=cosmos
export TEGALCHAIN_COSMOS_REST_URL="$COSMOS_URL"
export TEGALCHAIN_COSMOS_ANCHOR_PATH="${TEGALCHAIN_COSMOS_ANCHOR_PATH:-/tegalchain/gretelemetry/v1/anchor}"

require_mint_worker() {
  if ! curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
    echo "ERROR: mint worker not reachable at ${MINT_URL}" >&2
    echo "  Start: ./scripts/start-mint-worker.sh" >&2
    exit 1
  fi
}

require_cosmos_lab() {
  if ! curl -sf "${COSMOS_URL}/health" >/dev/null 2>&1; then
    echo "ERROR: Cosmos anchor lab not reachable at ${COSMOS_URL}" >&2
    echo "  Start: ./scripts/start-cosmos-anchor-lab.sh" >&2
    exit 1
  fi
}

ingest_one() {
  require_mint_worker
  echo "==> Ingest one Zeegate lab row → ${MINT_URL}"
  export MINT_WORKER_URL="$MINT_URL"
  "$PY" integrations/zeegate_telemetry/client.py
}

cosmos_drain() {
  require_cosmos_lab
  echo "==> Drain with TEGALCHAIN_SUBMITTER_BACKEND=cosmos (${COSMOS_URL})"
  "$PY" -m tegalchain.submitter drain --limit "${1:-10}"
  "$PY" -m tegalchain.submitter stats
}

verify_gtr() {
  local gtr_id="$1"
  echo "==> GET ${MINT_URL}/v1/telemetry/records/${gtr_id}"
  curl -sf "${MINT_URL}/v1/telemetry/records/${gtr_id}" | "$PY" -m json.tool | \
    "$PY" -c "
import json, sys
r = json.load(sys.stdin)
ref = r.get('ledger_ref') or ''
status = r.get('status')
print(f'status: {status}')
print(f'ledger_ref: {ref}')
if ref.startswith('LABMOCK-'):
    print('WARN: still mock ref — cosmos drain may not have processed this row')
    sys.exit(1)
if len(ref) < 32:
    print('WARN: ledger_ref looks too short for txhash')
    sys.exit(1)
print('OK: cosmos-style ledger_ref')
"
}

MODE="${1:-drain}"

case "$MODE" in
  ingest)
    ingest_one
    cosmos_drain "${2:-10}"
    echo
    echo "Use gtr_id from ingest output above:"
    echo "  ./scripts/phase5-cosmos-drain.sh verify <gtr_id>"
    ;;
  drain)
    cosmos_drain "${2:-10}"
    echo
    echo "Verify with gtr_id from pending ingest or queue:"
    echo "  ./scripts/phase5-cosmos-drain.sh verify <gtr_id>"
    ;;
  verify)
    GTR="${2:-}"
    if [[ -z "$GTR" ]]; then
      echo "Usage: $0 verify <gtr_id>" >&2
      exit 2
    fi
    require_mint_worker
    verify_gtr "$GTR"
    ;;
  *)
    echo "Usage: $0 [ingest|drain|verify <gtr_id>]" >&2
    exit 2
    ;;
esac
