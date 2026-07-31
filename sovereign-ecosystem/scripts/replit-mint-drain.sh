#!/usr/bin/env bash
# Phase 1c — drain mint queue (lab mock submitter by default; no Qortal required).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
export TEGALCHAIN_OUTBOX_DIR="${TEGALCHAIN_OUTBOX_DIR:-$ROOT/tegalchain/data/outbox}"
export TEGALCHAIN_SUBMITTER_BACKEND="${TEGALCHAIN_SUBMITTER_BACKEND:-mock}"

LIMIT="${1:-20}"
python -m tegalchain.submitter drain --limit "$LIMIT"
python -m tegalchain.submitter sla-check
