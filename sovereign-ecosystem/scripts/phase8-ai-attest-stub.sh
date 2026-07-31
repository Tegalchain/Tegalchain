#!/usr/bin/env bash
# Phase 8 — Zeegate CDR ↔ bandwidth TP-108 corroboration stub.
#
# Appends a signed THIRD_PARTY attestation (metadata.tp108) to an existing GTR.
#
# Usage:
#   ./scripts/phase8-ai-attest-stub.sh <gtr_id>
#   ./scripts/phase8-ai-attest-stub.sh            # uses latest LABEDGE001 gtr_id from queue DB
#
# With Phase 7 prod worker:
#   export MINT_WORKER_BEARER_TOKEN=<secret>
#   export MINT_WORKER_VALIDATE_TP108=1           # optional strict schema on worker
#
# Prerequisites:
#   - Mint worker on :8090 with an ingested Zeegate bandwidth GTR
#   - zeegate-cloud/cdr_adapter/fixtures/sample_cdr.csv (default corroboration inputs)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
GTR_ID="${1:-}"
TOKEN="${MINT_WORKER_BEARER_TOKEN:-}"

if [[ -n "$TOKEN" ]]; then
  # shellcheck source=scripts/phase7-bearer-env.sh
  source "$ROOT/scripts/phase7-bearer-env.sh"
  phase7_require_bearer_token || exit 1
fi

if ! curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
  echo "ERROR: mint worker not reachable at ${MINT_URL}" >&2
  exit 1
fi

export MINT_WORKER_URL="$MINT_URL"
export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export ZEEGATE_CDR_FIXTURE="${ZEEGATE_CDR_FIXTURE:-$ROOT/zeegate-cloud/cdr_adapter/fixtures/sample_cdr.csv}"
export PHASE8_GTR_ID="$GTR_ID"
export PHASE8_BEARER_TOKEN="$TOKEN"

echo "==> TP-108 Zeegate corroboration stub → ${MINT_URL}"
"$PY" -m ai_attestation_spec.zeegate_stub
