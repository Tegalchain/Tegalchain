#!/usr/bin/env bash
# Phase 7 — tegalid + Bearer ingest → drain → GLE + Carbon Account verify.
#
# Usage:
#   export MINT_WORKER_BEARER_TOKEN=<secret>
#   ./scripts/phase7-staging-ingest.sh
#
# Prerequisites:
#   - prod worker: ./scripts/restart-mint-worker-prod.sh
#   - TEGALID_BINDINGS_FILE pointing at lab bindings (default in prod start script)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
TOKEN="${MINT_WORKER_BEARER_TOKEN:-}"

# shellcheck source=scripts/phase7-bearer-env.sh
source "$ROOT/scripts/phase7-bearer-env.sh"
phase7_require_bearer_token || exit 1

if ! curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
  echo "ERROR: mint worker not reachable at ${MINT_URL}" >&2
  exit 1
fi

export MINT_WORKER_URL="$MINT_URL"
export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export TEGALCHAIN_OUTBOX_DIR="${TEGALCHAIN_OUTBOX_DIR:-$ROOT/tegalchain/data/outbox}"

SOURCE_ID="did:tegal:LABEDGE001"
export PHASE7_CARBON_SOURCE_ID="$SOURCE_ID"

echo "==> POST tegalid-bound Zeegate telemetry (Bearer) → ${MINT_URL}"
INGEST_OUT="$("$PY" <<'PY'
import json
import os
import sys
import time

from greentelemetry_protocol_spec.signing import sign_payload
from integrations.mint_worker.submit import submit_telemetry

LAB_HMAC = bytes.fromhex("736f7665726569676e2d6c61622d686d61632d7365637265743031")
unsigned = {
    "node_id": "did:tegal:LABEDGE001",
    "project_id": "zeegate-telecom",
    "binding_id": "edge-sim-01",
    "timestamp": int(time.time()),
    "system_type": "ZEEGATE_TELECOM",
    "metrics": {"telecom_bandwidth_bytes": 1048576},
}
canonical = json.dumps(unsigned, separators=(",", ":"), sort_keys=True)
unsigned["signature"] = sign_payload(canonical, LAB_HMAC)
result = submit_telemetry(os.environ["MINT_WORKER_URL"], unsigned)
print(json.dumps(result))
PY
)"
echo "$INGEST_OUT"

GTR_ID="$("$PY" -c "
import json, re, sys
text = sys.stdin.read()
for pattern in (
    r'\"gtr_id\": \"([0-9a-f-]{36})\"',
    r\"'gtr_id': '([0-9a-f-]{36})'\",
):
    m = re.search(pattern, text)
    if m:
        print(m.group(1))
        raise SystemExit(0)
data = json.loads(text)
print(
    data.get('gtr', {}).get('gtr_id')
    or data.get('block_candidate', {}).get('gtr_id')
    or data.get('gtr_id', '')
)
" <<<"$INGEST_OUT")"

if [[ -z "$GTR_ID" ]]; then
  echo "ERROR: could not extract gtr_id from ingest response" >&2
  exit 1
fi
echo "==> gtr_id: ${GTR_ID}"

echo "==> Mock drain (archive GLE + Carbon Account)"
bash ./scripts/replit-mint-drain.sh 10

echo "==> GET ${MINT_URL}/v1/telemetry/records/${GTR_ID}"
RECORD="$(curl -sf -H "Authorization: Bearer ${TOKEN}" \
  "${MINT_URL}/v1/telemetry/records/${GTR_ID}")"
echo "$RECORD" | "$PY" -m json.tool | grep -E '"status"|greenledger_entry|por_scores|protocol_standard' || true

GLE="$("$PY" -c "import json,sys; print('yes' if json.load(sys.stdin).get('greenledger_entry') else 'no')" <<<"$RECORD")"
if [[ "$GLE" != "yes" ]]; then
  echo "ERROR: greenledger_entry missing after drain" >&2
  exit 1
fi
echo "OK: GLE archived on record"

echo "==> GET ${MINT_URL}/v1/greenledger/carbon-accounts/${SOURCE_ID}"
CARBON="$(curl -sf -H "Authorization: Bearer ${TOKEN}" \
  "${MINT_URL}/v1/greenledger/carbon-accounts/${SOURCE_ID}")"
echo "$CARBON" | "$PY" -m json.tool | grep -E 'protocol_standard|source_id|data_completeness' || true
echo "OK: Phase 7 staging ingest complete"
