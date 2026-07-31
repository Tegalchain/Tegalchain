#!/usr/bin/env bash
# Start Phase 5 lab Cosmos anchor (FastAPI on :1317 by default).
# Usage: ./scripts/start-cosmos-anchor-lab.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

HOST="${COSMOS_ANCHOR_LAB_HOST:-127.0.0.1}"
PORT="${COSMOS_ANCHOR_LAB_PORT:-1317}"
URL="http://${HOST}:${PORT}"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

if curl -sf "${URL}/health" >/dev/null 2>&1; then
  echo "Cosmos anchor lab already listening on ${URL}"
  curl -s "${URL}/health" | "$PY" -m json.tool
  exit 0
fi

if ! "$PY" -c "import fastapi, uvicorn" 2>/dev/null; then
  echo "==> Installing Python deps..."
  "$PY" -m pip install -r requirements.txt
fi

echo "==> Starting Cosmos anchor lab on ${URL}"
echo "    Health: curl -s ${URL}/health"
echo "    Anchor: POST ${URL}/tegalchain/gretelemetry/v1/anchor"
echo "    Leave this tab running — Ctrl+C stops the server."
exec "$PY" -m integrations.cosmos_anchor_lab
