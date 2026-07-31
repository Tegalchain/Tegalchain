#!/usr/bin/env bash
# Phase 6 — verify TP-102 PoR (RFM) scores on ingested GTRs.
#
# Usage:
#   ./scripts/phase6-verify-por.sh ingest          # POST Zeegate row + verify por_scores
#   ./scripts/phase6-verify-por.sh verify <gtr_id> # verify existing record
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

require_worker() {
  if ! curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
    echo "ERROR: mint worker not reachable at ${MINT_URL}" >&2
    echo "  Start: ./scripts/start-mint-worker.sh" >&2
    exit 1
  fi
  if ! "$PY" -c "
import json, sys, urllib.request
with urllib.request.urlopen('${MINT_URL}/health', timeout=5) as resp:
    health = json.load(resp)
features = health.get('features') or []
if 'por_scores' not in features:
    print('ERROR: mint worker is running stale code (GET por_scores not enabled)', file=sys.stderr)
    print('  Restart after git pull: ./scripts/restart-mint-worker.sh', file=sys.stderr)
    print(f\"  health mint_worker_version={health.get('mint_worker_version')!r}\", file=sys.stderr)
    raise SystemExit(1)
" 2>&1; then
    exit 1
  fi
}

validate_por_json() {
  local por_json="$1"
  "$PY" -c "
import json, sys
from proof_of_resonance_spec.validate import validate_por_payload
por = json.loads(sys.argv[1])
validate_por_payload(por)
print('protocol_standard:', por.get('protocol_standard'))
print('eqs:', por.get('eqs'))
print('riv:', por.get('riv'))
print('resonance_score:', por.get('resonance_score'))
print('scoring_profile:', por.get('scoring_profile'))
print('OK: TP-102 schema valid')
" "$por_json"
}

verify_gtr_por() {
  local gtr_id="$1"
  echo "==> GET ${MINT_URL}/v1/telemetry/records/${gtr_id}"
  local body
  body="$(curl -sf "${MINT_URL}/v1/telemetry/records/${gtr_id}")"
  echo "$body" | "$PY" -m json.tool | grep -E '"protocol_standard"|"eqs"|"riv"|"resonance_score"|evidence_kind|system_type' || true
  local por
  por="$("$PY" -c "import json,sys; print(json.dumps(json.load(sys.stdin).get('por_scores')))" <<<"$body")"
  if [[ "$por" == "null" ]]; then
    echo "ERROR: por_scores missing on record" >&2
    echo "  If ingest shows tp102_rfm but GET does not, restart the mint worker:" >&2
    echo "    ./scripts/restart-mint-worker.sh" >&2
    exit 1
  fi
  echo "==> Validate por_scores against proof-of-resonance-spec/schema.json"
  validate_por_json "$por"
}

ingest_and_verify() {
  require_worker
  echo "==> Ingest Zeegate lab row → ${MINT_URL}"
  export MINT_WORKER_URL="$MINT_URL"
  local out
  out="$("$PY" integrations/zeegate_telemetry/client.py)"
  echo "$out"
  local gtr_id
  gtr_id="$("$PY" -c "
import ast
import re
import sys

text = sys.stdin.read().strip()
if not text:
    print('ERROR: empty ingest response', file=sys.stderr)
    raise SystemExit(1)
for pattern in (
    r\"'gtr_id': '([0-9a-f-]{36})'\",
    r'\"gtr_id\": \"([0-9a-f-]{36})\"',
):
    match = re.search(pattern, text)
    if match:
        print(match.group(1))
        raise SystemExit(0)
data = ast.literal_eval(text)
for path in (
    ('gtr', 'gtr_id'),
    ('block_candidate', 'gtr_id'),
    ('mint', 'gtr_id'),
    ('gtr_id',),
):
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            break
        cur = cur[key]
    else:
        print(cur)
        raise SystemExit(0)
sys.stderr.write('ERROR: gtr_id not found in ingest response\n')
raise SystemExit(1)
" <<<"$out")"
  echo "==> gtr_id: ${gtr_id}"
  verify_gtr_por "$gtr_id"
}

MODE="${1:-ingest}"

case "$MODE" in
  ingest)
    ingest_and_verify
    ;;
  verify)
    GTR="${2:-}"
    if [[ -z "$GTR" ]]; then
      echo "Usage: $0 verify <gtr_id>" >&2
      exit 2
    fi
    require_worker
    verify_gtr_por "$GTR"
    ;;
  *)
    echo "Usage: $0 [ingest|verify <gtr_id>]" >&2
    exit 2
    ;;
esac
