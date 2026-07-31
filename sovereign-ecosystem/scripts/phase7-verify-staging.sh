#!/usr/bin/env bash
# Phase 7 — verify staging profile: Bearer auth, ops routes, Carbon Account, integrity.
#
# Usage:
#   ./scripts/phase7-verify-staging.sh           # lab worker (no bearer)
#   ./scripts/phase7-verify-staging.sh staging   # bearer required (prod profile)
#
# Prerequisites:
#   - mint worker on :8090
#   - for carbon/integrity checks: at least one drained GLE in queue DB
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
MODE="${1:-lab}"
TOKEN="${MINT_WORKER_BEARER_TOKEN:-}"

auth_args=()
if [[ -n "$TOKEN" ]]; then
  auth_args=(-H "Authorization: Bearer ${TOKEN}")
fi

require_worker() {
  if ! curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
    echo "ERROR: mint worker not reachable at ${MINT_URL}" >&2
    echo "  Lab: ./scripts/start-mint-worker.sh" >&2
    echo "  Staging: export MINT_WORKER_BEARER_TOKEN=... && ./scripts/start-mint-worker-prod.sh" >&2
    exit 1
  fi
}

check_health() {
  echo "==> GET ${MINT_URL}/health"
  curl -sf "${MINT_URL}/health" | "$PY" -m json.tool | grep -E '"status"|mint_worker_version|identity_mode|bearer_required|features' || true
}

check_bearer_enforcement() {
  echo "==> Bearer enforcement (staging profile)"
  local code
  if [[ "$MODE" == "staging" ]]; then
    # shellcheck source=scripts/phase7-bearer-env.sh
    source "$ROOT/scripts/phase7-bearer-env.sh"
    phase7_require_bearer_token || exit 1
    local bearer_required identity_mode
    bearer_required="$("$PY" -c "import json,sys,urllib.request; h=json.load(urllib.request.urlopen('${MINT_URL}/health')); print('true' if h.get('bearer_required') else 'false')")"
    identity_mode="$("$PY" -c "import json,sys,urllib.request; h=json.load(urllib.request.urlopen('${MINT_URL}/health')); print(h.get('identity_mode',''))")"
    if [[ "$bearer_required" != "true" ]]; then
      echo "ERROR: health.bearer_required is not true — restart with start-mint-worker-prod.sh" >&2
      exit 1
    fi
    if [[ "$identity_mode" != "tegalid" ]]; then
      echo "WARN: identity_mode=${identity_mode} (expected tegalid for staging)"
    fi
    for path in /v1/queue/stats /v1/queue/anchor-sla "/v1/greenledger/carbon-accounts/_probe"; do
      code="$(curl -s -o /dev/null -w '%{http_code}' "${MINT_URL}${path}")"
      if [[ "$code" != "401" ]]; then
        echo "ERROR: expected 401 on ${path} without Bearer (got ${code})" >&2
        exit 1
      fi
    done
    code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "${MINT_URL}/v1/telemetry" \
      -H 'Content-Type: application/json' -d '{}')"
    if [[ "$code" != "401" ]]; then
      echo "ERROR: expected 401 on POST /v1/telemetry without Bearer (got ${code})" >&2
      exit 1
    fi
    code="$(curl -s "${auth_args[@]}" -o /dev/null -w '%{http_code}' "${MINT_URL}/v1/queue/stats")"
    if [[ "$code" != "200" ]]; then
      echo "ERROR: expected 200 on /v1/queue/stats with Bearer (got ${code})" >&2
      exit 1
    fi
    echo "OK: telemetry, queue, and greenledger routes require Bearer"
  else
    code="$(curl -s -o /dev/null -w '%{http_code}' "${MINT_URL}/v1/queue/stats")"
    if [[ "$code" == "401" ]]; then
      echo "WARN: queue routes returned 401 — worker may be in prod profile; pass 'staging' + token"
    else
      echo "OK: lab worker allows unauthenticated queue stats"
    fi
  fi
}

check_anchor_sla() {
  echo "==> GET ${MINT_URL}/v1/queue/anchor-sla"
  local body violations
  body="$(curl -sf "${auth_args[@]}" "${MINT_URL}/v1/queue/anchor-sla")"
  violations="$("$PY" -c "import json,sys; print(json.load(sys.stdin).get('violation_count', 0))" <<<"$body")"
  echo "$body" | "$PY" -m json.tool | grep -E 'violation_count|pending_count|sla_seconds' || true
  if [[ "$violations" -gt 0 ]]; then
    echo "WARN: anchor SLA violations detected (${violations})"
  else
    echo "OK: anchor SLA clear"
  fi
}

check_integrity() {
  echo "==> python -m tegalchain.greenledger integrity-check"
  if ! "$PY" -m tegalchain.greenledger integrity-check --schedule DAILY; then
    local exit_code=$?
    if [[ "$exit_code" -eq 2 ]]; then
      echo "ERROR: integrity violations reported" >&2
      exit 2
    fi
    exit "$exit_code"
  fi
  echo "OK: integrity check passed"
}

check_carbon_account() {
  echo "==> Carbon Account HTTP (if GLE archived)"
  local source_id="${PHASE7_CARBON_SOURCE_ID:-zerocell-node-001}"
  local code body
  code="$(curl -s "${auth_args[@]}" -o /dev/null -w '%{http_code}' \
    "${MINT_URL}/v1/greenledger/carbon-accounts/${source_id}")"
  if [[ "$code" == "404" ]]; then
    echo "SKIP: no carbon account for ${source_id} — drain queue first to archive GLE"
    return 0
  fi
  if [[ "$code" != "200" ]]; then
    echo "ERROR: carbon account GET returned ${code}" >&2
    exit 1
  fi
  body="$(curl -sf "${auth_args[@]}" "${MINT_URL}/v1/greenledger/carbon-accounts/${source_id}")"
  echo "$body" | "$PY" -m json.tool | grep -E 'protocol_standard|source_id|net_emissions|data_completeness' || true
  echo "OK: carbon account API"
}

check_cold_export() {
  echo "==> python -m tegalchain.greenledger export-cold"
  local out
  out="$("$PY" -m tegalchain.greenledger export-cold --output-dir "$ROOT/tegalchain/data/cold_export")"
  echo "$out"
  echo "OK: cold-tier export job ran (0 rows is normal in hot-only lab)"
}

require_worker
check_health
check_bearer_enforcement
check_anchor_sla
check_integrity
check_carbon_account
check_cold_export
echo
echo "Phase 7 staging checks complete (${MODE} profile)"
