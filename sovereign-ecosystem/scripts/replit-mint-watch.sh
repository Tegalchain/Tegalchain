#!/usr/bin/env bash
# Phase 1 operational closure — periodic drain + anchor SLA monitoring on Replit.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export TEGALCHAIN_OUTBOX_DIR="${TEGALCHAIN_OUTBOX_DIR:-$ROOT/tegalchain/data/outbox}"
export TEGALCHAIN_SUBMITTER_BACKEND="${TEGALCHAIN_SUBMITTER_BACKEND:-mock}"

LOG_FILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --log)
      LOG_FILE="${2:-}"
      shift 2
      ;;
    *)
      break
      ;;
  esac
done

LIMIT="${1:-20}"
INTERVAL="${2:-30}"
CYCLES="${3:-}"
INTEGRITY="${PHASE7_INTEGRITY:-0}"

WATCH_ARGS=(watch --limit "$LIMIT" --interval "$INTERVAL" --json)
if [[ "$INTEGRITY" == "1" ]]; then
  WATCH_ARGS+=(--integrity)
fi
if [[ -n "$CYCLES" ]]; then
  WATCH_ARGS+=(--cycles "$CYCLES")
fi
if [[ -n "$LOG_FILE" ]]; then
  WATCH_ARGS+=(--log "$LOG_FILE")
fi

exec python -m tegalchain.submitter "${WATCH_ARGS[@]}"
