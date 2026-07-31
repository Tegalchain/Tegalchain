#!/usr/bin/env bash
# Phase 2 — watch FreeSWITCH CDR CSV and publish adapter-normalized GTRs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export ZEEGATE_CDR_DIR="${ZEEGATE_CDR_DIR:-/var/log/freeswitch/cdr-csv}"
export ZEEGATE_CDR_STATE_DB="${ZEEGATE_CDR_STATE_DB:-$ROOT/tegalchain/data/cdr_watcher.db}"

CMD="${1:-once}"
INTERVAL="${2:-15}"
CYCLES="${3:-}"

if [[ "$CMD" == "watch" && -n "$CYCLES" ]]; then
  exec env PYTHONPATH="$ROOT/zeegate-cloud" python -m cdr_adapter watch \
    --interval "$INTERVAL" --cycles "$CYCLES"
fi

if [[ "$CMD" == "watch" ]]; then
  exec env PYTHONPATH="$ROOT/zeegate-cloud" python -m cdr_adapter watch \
    --interval "$INTERVAL"
fi

exec env PYTHONPATH="$ROOT/zeegate-cloud" python -m cdr_adapter once
