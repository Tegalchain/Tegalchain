#!/usr/bin/env bash
# Phase 7 — verify 24h staging soak completion from soak_watch JSONL log.
#
# Usage:
#   ./scripts/phase7-soak-verify.sh
#   REPLIT_SOAK_HOURS=1 ./scripts/phase7-soak-verify.sh   # lab shortcut
#   export MINT_WORKER_BEARER_TOKEN=...  # optional: also run phase7-verify-staging.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

SOAK_LOG="${PHASE7_SOAK_LOG:-$ROOT/tegalchain/data/soak_watch.log}"
SOAK_HOURS="${REPLIT_SOAK_HOURS:-24}"

if [[ ! -f "$SOAK_LOG" ]]; then
  echo "FAIL: soak log missing: $SOAK_LOG" >&2
  echo "  Run: ./scripts/phase7-soak-watch.sh" >&2
  exit 1
fi

"$PY" - "$SOAK_LOG" "$SOAK_HOURS" <<'PY'
import json
import sys
from datetime import UTC, datetime

log_path, hours_str = sys.argv[1], sys.argv[2]
required_hours = float(hours_str)


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


soak_start: dict | None = None
cycles: list[tuple[int, dict]] = []

with open(log_path, encoding="utf-8") as handle:
    for lineno, raw in enumerate(handle, 1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON at line {lineno}: {exc}")
        if obj.get("event") == "soak_start":
            soak_start = obj
            continue
        if "cycle" in obj:
            cycles.append((lineno, obj))

if not cycles:
    fail("no watch cycles in log (run ./scripts/phase7-soak-watch.sh)")

for lineno, obj in cycles:
    cycle_no = obj.get("cycle")
    sla_count = obj.get("sla", {}).get("violation_count", 0)
    if sla_count > 0:
        fail(f"SLA violation at line {lineno} cycle {cycle_no}: violation_count={sla_count}")
    integrity = obj.get("integrity")
    if integrity is not None:
        integrity_count = integrity.get("violation_count", 0)
        if integrity_count > 0:
            fail(
                f"integrity violation at line {lineno} cycle {cycle_no}: "
                f"violation_count={integrity_count}"
            )

integrity_runs = sum(1 for _, obj in cycles if "integrity" in obj)
if integrity_runs < 1:
    fail("no integrity cycles in log (soak watch must use PHASE7_INTEGRITY=1)")

timestamps: list[datetime] = []
for _, obj in cycles:
    ts_raw = obj.get("logged_at") or obj.get("sla", {}).get("checked_at")
    if isinstance(ts_raw, str) and ts_raw.strip():
        timestamps.append(parse_ts(ts_raw))

if not timestamps:
    fail("no timestamps in cycle log lines")

start_ts = timestamps[0]
if soak_start and isinstance(soak_start.get("started_at"), str):
    start_ts = parse_ts(soak_start["started_at"])

end_ts = timestamps[-1]
span_hours = (end_ts - start_ts).total_seconds() / 3600.0

if span_hours < required_hours:
    fail(
        f"log span {span_hours:.2f}h < required {required_hours}h "
        f"(started {start_ts.isoformat()}, last cycle {end_ts.isoformat()})"
    )

print(f"OK: soak log {log_path}")
print(f"  cycles={len(cycles)} integrity_runs={integrity_runs} span={span_hours:.2f}h")
if soak_start and soak_start.get("target_end_at"):
    print(f"  soak_start={soak_start['started_at']} target_end={soak_start['target_end_at']}")
PY

if [[ -n "${MINT_WORKER_BEARER_TOKEN:-}" ]]; then
  echo "==> phase7-verify-staging.sh staging (MINT_WORKER_BEARER_TOKEN set)"
  "$ROOT/scripts/phase7-verify-staging.sh" staging
else
  echo "SKIP: phase7-verify-staging.sh (set MINT_WORKER_BEARER_TOKEN to include)"
fi
