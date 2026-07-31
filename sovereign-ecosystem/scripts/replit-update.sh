#!/usr/bin/env bash
# Pull latest origin/main on Replit and verify Phase 7/8 scripts + deps.
#
# Run inside Replit Shell:
#   cd ~/workspace/sovereign-ecosystem
#   ./scripts/replit-update.sh
#
# Or one-liner (before first local copy of this script):
#   curl -fsSL https://raw.githubusercontent.com/Shootle/sovereign-ecosystem/main/scripts/replit-update.sh | bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

RESTART_WORKER="${REPLIT_UPDATE_RESTART:-0}"
EXPECT_COMMIT="${REPLIT_EXPECT_COMMIT:-}"

echo "==> Replit update: $ROOT"
BEFORE="$(git rev-parse HEAD)"
echo "==> Before: $BEFORE ($(git log -1 --oneline))"

git fetch origin main
BEHIND="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
if [[ "$BEHIND" -eq 0 ]]; then
  echo "OK: already at origin/main"
else
  echo "==> Pulling ${BEHIND} commit(s) from origin/main"
  git pull origin main
fi

AFTER="$(git rev-parse HEAD)"
echo "==> After:  $AFTER ($(git log -1 --oneline))"

if [[ "$BEFORE" != "$AFTER" ]]; then
  echo "==> Updated $(git rev-list --count "${BEFORE}..${AFTER}") commit(s)"
fi

SYNC_ARGS=()
if [[ -n "$EXPECT_COMMIT" ]]; then
  SYNC_ARGS+=(--expect-commit "$EXPECT_COMMIT")
fi
./scripts/replit-sync-check.sh "${SYNC_ARGS[@]}"

if [[ -f requirements.txt ]]; then
  # shellcheck source=scripts/replit-ensure-deps.sh
  source "$ROOT/scripts/replit-ensure-deps.sh"
  PY="${REPLIT_PY:-$PY}"
fi

MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
if curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
  HEALTH="$("$PY" -c "
import json, urllib.request
print(json.dumps(json.load(urllib.request.urlopen('${MINT_URL}/health')), indent=2))
" 2>/dev/null || echo '{}')"
  echo "==> Running mint worker detected on ${MINT_URL}"
  echo "$HEALTH" | "$PY" -m json.tool | grep -E '"mint_worker_version"|"features"|"bearer_required"' || true
  if [[ "$RESTART_WORKER" == "1" ]]; then
    if [[ -n "${MINT_WORKER_BEARER_TOKEN:-}" ]] && [[ -x scripts/restart-mint-worker-prod.sh ]]; then
      echo "==> Restarting prod mint worker (REPLIT_UPDATE_RESTART=1)"
      ./scripts/restart-mint-worker-prod.sh
    elif [[ -x scripts/start-mint-worker.sh ]]; then
      echo "==> Restarting lab mint worker (REPLIT_UPDATE_RESTART=1)"
      pkill -f 'integrations.mint_worker' 2>/dev/null || true
      nohup "$PY" -m integrations.mint_worker >/tmp/mint-worker.log 2>&1 &
      sleep 1
    fi
  else
    echo "TIP: restart mint worker after pull so new routes/features load:"
    echo "  export MINT_WORKER_BEARER_TOKEN=... && ./scripts/restart-mint-worker-prod.sh"
    echo "  or: REPLIT_UPDATE_RESTART=1 ./scripts/replit-update.sh"
  fi
else
  echo "SKIP: mint worker not running"
fi

echo
echo "Replit update complete — HEAD ${AFTER}"
