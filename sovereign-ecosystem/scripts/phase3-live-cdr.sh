#!/usr/bin/env bash
# Phase 3 — sync Docker zeegate_cdr volume → adapter → mint worker (optional drain).
#
# Prerequisites:
#   - Mint worker on :8090 (TEGALCHAIN_IDENTITY_MODE=dev)
#   - Voice stack up (zeegate-cloud/deploy ./up.sh)
#   - At least one completed SIP call so CDR CSV exists in volume zeegate_cdr
#
# Usage:
#   ./scripts/phase3-live-cdr.sh              # sync + ingest once
#   ./scripts/phase3-live-cdr.sh drain          # sync + ingest + mock drain
#   ./scripts/phase3-live-cdr.sh inspect      # list CDR volume only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CDR_LIVE_DIR="${ZEEGATE_CDR_LIVE_DIR:-/tmp/zeegate-cdr-live}"
CDR_VOLUME="${ZEEGATE_CDR_VOLUME:-zeegate_cdr}"
MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
MODE="${1:-once}"

inspect_volume() {
  echo "==> Docker volume ${CDR_VOLUME} (recursive):"
  docker run --rm -v "${CDR_VOLUME}:/cdr:ro" alpine ls -laR /cdr 2>/dev/null || true
}

resolve_cdr_watch_dir() {
  local csv
  csv="$(find "$CDR_LIVE_DIR" -type f -name '*.csv' 2>/dev/null | head -1 || true)"
  if [[ -n "$csv" ]]; then
    dirname "$csv"
  elif compgen -G "${CDR_LIVE_DIR}/*.csv" >/dev/null 2>&1; then
    echo "$CDR_LIVE_DIR"
  elif compgen -G "${CDR_LIVE_DIR}/cdr-csv/*.csv" >/dev/null 2>&1; then
    echo "${CDR_LIVE_DIR}/cdr-csv"
  else
    echo "$CDR_LIVE_DIR"
  fi
}

sync_cdr_from_volume() {
  mkdir -p "$CDR_LIVE_DIR"
  if ! docker volume inspect "$CDR_VOLUME" >/dev/null 2>&1; then
    echo "ERROR: Docker volume '$CDR_VOLUME' not found. Run: cd zeegate-cloud/deploy && ./up.sh" >&2
    exit 1
  fi
  docker run --rm -v "${CDR_VOLUME}:/cdr:ro" -v "${CDR_LIVE_DIR}:/out" alpine \
    sh -c 'cp -a /cdr/. /out/ 2>/dev/null || true; chmod -R a+rX /out'
  echo "==> CDR sync: volume ${CDR_VOLUME} → ${CDR_LIVE_DIR}"
  ls -la "$CDR_LIVE_DIR" || true
  find "$CDR_LIVE_DIR" -type f -name '*.csv' -ls 2>/dev/null || true
}

case "$MODE" in
  inspect)
    inspect_volume
    exit 0
    ;;
  once|drain)
    sync_cdr_from_volume
    WATCH_DIR="$(resolve_cdr_watch_dir)"
    if ! compgen -G "${WATCH_DIR}/*.csv" >/dev/null 2>&1; then
      echo "WARNING: No *.csv under ${WATCH_DIR}." >&2
      echo "  Place a test SIP call first (edge001@zeegate.lab or lab1000 dial 1000)." >&2
      echo "  Replit often blocks UDP SIP — try WSL/local Docker + LAN softphone." >&2
      echo "  Tip: ZEEGATE_CDR_FALLBACK_SOURCE=edge001 (default) for tegalid mapping." >&2
      inspect_volume
    fi
    export ZEEGATE_CDR_DIR="$WATCH_DIR"
    export MINT_WORKER_URL="$MINT_URL"
    export ZEEGATE_CDR_FALLBACK_SOURCE="${ZEEGATE_CDR_FALLBACK_SOURCE:-edge001}"
    export TEGALCHAIN_MINT_QUEUE_DB="${TEGALCHAIN_MINT_QUEUE_DB:-$ROOT/tegalchain/data/mint_queue.db}"
    ./scripts/zeegate-cdr-watch.sh once
    if [[ "$MODE" == "drain" ]]; then
      bash ./scripts/replit-mint-drain.sh 5
    fi
    ;;
  *)
    echo "Usage: $0 [once|drain|inspect]" >&2
    exit 2
    ;;
esac
