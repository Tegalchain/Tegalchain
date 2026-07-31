#!/usr/bin/env bash
# Phase 7 — 24h staging soak watch with JSONL audit log.
#
# Usage:
#   ./scripts/phase7-soak-watch.sh [limit] [interval]
#   REPLIT_SOAK_HOURS=1 ./scripts/phase7-soak-watch.sh 20 30   # lab shortcut
#
# Log: PHASE7_SOAK_LOG (default tegalchain/data/soak_watch.log)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

LIMIT="${1:-20}"
INTERVAL="${2:-30}"
SOAK_LOG="${PHASE7_SOAK_LOG:-$ROOT/tegalchain/data/soak_watch.log}"
SOAK_HOURS="${REPLIT_SOAK_HOURS:-24}"

mkdir -p "$(dirname "$SOAK_LOG")"

START_ISO="$("$PY" - <<'PY'
from datetime import UTC, datetime, timedelta
import os

hours = float(os.environ.get("REPLIT_SOAK_HOURS", "24"))
start = datetime.now(UTC)
end = start + timedelta(hours=hours)
print(start.isoformat().replace("+00:00", "Z"))
print(end.isoformat().replace("+00:00", "Z"))
print(hours)
PY
)"

START_AT="$(echo "$START_ISO" | sed -n '1p')"
TARGET_END="$(echo "$START_ISO" | sed -n '2p')"

"$PY" - <<PY >>"$SOAK_LOG"
import json

payload = {
    "event": "soak_start",
    "started_at": "${START_AT}",
    "target_hours": ${SOAK_HOURS},
    "target_end_at": "${TARGET_END}",
    "limit": ${LIMIT},
    "interval": ${INTERVAL},
    "integrity": True,
}
print(json.dumps(payload, separators=(",", ":")))
PY

echo "==> Phase 7 soak watch"
echo "    log:         $SOAK_LOG"
echo "    started:     $START_AT"
echo "    target end:  $TARGET_END (${SOAK_HOURS}h)"
echo "    limit/cycle: $LIMIT"
echo "    interval:    ${INTERVAL}s"
echo "    integrity:   PHASE7_INTEGRITY=1 (each cycle)"
echo
echo "Stop with Ctrl+C; verify with: ./scripts/phase7-soak-verify.sh"
echo

export PHASE7_INTEGRITY=1
exec "$ROOT/scripts/replit-mint-watch.sh" --log "$SOAK_LOG" "$LIMIT" "$INTERVAL"
