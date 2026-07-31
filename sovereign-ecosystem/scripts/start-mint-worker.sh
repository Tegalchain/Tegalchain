#!/usr/bin/env bash
# Start the Phase 1/2 mint worker on Replit, WSL, or local lab.
# Usage: ./scripts/start-mint-worker.sh
# Leave this shell open — the worker runs in the foreground.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "ERROR: python3 not found on PATH" >&2
  exit 127
fi

if ! "$PY" -c "import fastapi, uvicorn" 2>/dev/null; then
  # shellcheck source=scripts/replit-ensure-deps.sh
  source "$ROOT/scripts/replit-ensure-deps.sh"
  PY="${REPLIT_PY:-$PY}"
fi

export TEGALCHAIN_IDENTITY_MODE="${TEGALCHAIN_IDENTITY_MODE:-dev}"
export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export TEGALCHAIN_OUTBOX_DIR="${TEGALCHAIN_OUTBOX_DIR:-$ROOT/tegalchain/data/outbox}"

mkdir -p "$(dirname "$TEGALCHAIN_MINT_QUEUE_DB")" "$TEGALCHAIN_OUTBOX_DIR"

if curl -sf http://127.0.0.1:8090/health >/dev/null 2>&1; then
  echo "Mint worker already listening on :8090"
  curl -s http://127.0.0.1:8090/health | "$PY" -m json.tool
  exit 0
fi

echo "==> Starting mint worker (repo: $ROOT)"
echo "    Python: $("$PY" --version)"
echo "    Health: curl -s http://127.0.0.1:8090/health"
echo "    Leave this tab running — Ctrl+C stops the worker."
exec "$PY" -m integrations.mint_worker
