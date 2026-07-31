#!/usr/bin/env bash
# Start mint worker with Phase 7 production/staging profile.
# Usage:
#   export MINT_WORKER_BEARER_TOKEN=<secret>
#   ./scripts/start-mint-worker-prod.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

if [[ -z "${MINT_WORKER_BEARER_TOKEN:-}" ]]; then
  echo "ERROR: MINT_WORKER_BEARER_TOKEN must be set for prod/staging profile" >&2
  echo "  Example: export MINT_WORKER_BEARER_TOKEN=\$(openssl rand -hex 24)" >&2
  exit 1
fi

export TEGALCHAIN_IDENTITY_MODE="${TEGALCHAIN_IDENTITY_MODE:-tegalid}"
export TEGALCHAIN_REQUIRE_BEARER="${TEGALCHAIN_REQUIRE_BEARER:-1}"
export TEGALID_BINDINGS_FILE="${TEGALID_BINDINGS_FILE:-$ROOT/tegalchain/data/tegalid_bindings.example.json}"
export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export TEGALCHAIN_OUTBOX_DIR="${TEGALCHAIN_OUTBOX_DIR:-$ROOT/tegalchain/data/outbox}"
export TEGALCHAIN_SUBMITTER_BACKEND="${TEGALCHAIN_SUBMITTER_BACKEND:-mock}"

if [[ ! -f "$TEGALID_BINDINGS_FILE" ]]; then
  echo "ERROR: TEGALID_BINDINGS_FILE not found: $TEGALID_BINDINGS_FILE" >&2
  exit 1
fi

if curl -sf http://127.0.0.1:8090/health >/dev/null 2>&1; then
  echo "Mint worker already listening on :8090 — use ./scripts/restart-mint-worker-prod.sh" >&2
  exit 1
fi

if ! "$PY" -c "import fastapi, uvicorn" 2>/dev/null; then
  # shellcheck source=scripts/replit-ensure-deps.sh
  source "$ROOT/scripts/replit-ensure-deps.sh"
  PY="${REPLIT_PY:-$PY}"
fi

mkdir -p "$(dirname "$TEGALCHAIN_MINT_QUEUE_DB")" "$TEGALCHAIN_OUTBOX_DIR"

echo "==> Starting mint worker (prod/staging profile)"
echo "    identity_mode=$TEGALCHAIN_IDENTITY_MODE"
echo "    bearer_required=$TEGALCHAIN_REQUIRE_BEARER"
echo "    bindings=$TEGALID_BINDINGS_FILE"
echo "    Health: curl -s http://127.0.0.1:8090/health | $PY -m json.tool"
exec "$PY" -m integrations.mint_worker
