#!/usr/bin/env bash
# Verify Replit workspace is synced with origin/main and Phase 7 scripts exist.
#
# Usage:
#   ./scripts/replit-sync-check.sh
#   ./scripts/replit-sync-check.sh --expect-commit 3346af3
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  PY=python
fi

EXPECT_COMMIT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --expect-commit)
      EXPECT_COMMIT="${2:-}"
      shift 2
      ;;
    *)
      echo "Usage: $0 [--expect-commit <sha>]" >&2
      exit 2
      ;;
  esac
done

echo "==> Repo: $ROOT"
echo "==> Branch: $(git rev-parse --abbrev-ref HEAD)"
HEAD="$(git rev-parse HEAD)"
echo "==> HEAD: $HEAD"

if ! git fetch origin main --quiet 2>/dev/null; then
  echo "WARN: could not fetch origin/main (offline?)"
else
  BEHIND="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
  AHEAD="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
  if [[ "$BEHIND" -gt 0 ]]; then
    echo "ERROR: local main is ${BEHIND} commit(s) behind origin/main — run: git pull origin main" >&2
    exit 1
  fi
  if [[ "$AHEAD" -gt 0 ]]; then
    echo "WARN: local main is ${AHEAD} commit(s) ahead of origin/main"
  else
    echo "OK: up to date with origin/main"
  fi
fi

if [[ -n "$EXPECT_COMMIT" ]] && [[ "$HEAD" != "$EXPECT_COMMIT"* ]]; then
  echo "WARN: HEAD does not match --expect-commit ${EXPECT_COMMIT}"
fi

REQUIRED_SCRIPTS=(
  scripts/start-mint-worker.sh
  scripts/start-mint-worker-prod.sh
  scripts/restart-mint-worker-prod.sh
  scripts/phase7-verify-staging.sh
  scripts/phase7-staging-ingest.sh
  scripts/phase7-bearer-env.sh
  scripts/phase8-ai-attest-stub.sh
  scripts/replit-mint-drain.sh
  scripts/replit-mint-watch.sh
  scripts/phase7-soak-watch.sh
  scripts/phase7-soak-verify.sh
  scripts/replit-update.sh
)

echo "==> Phase scripts"
for script in "${REQUIRED_SCRIPTS[@]}"; do
  if [[ ! -f "$script" ]]; then
    echo "ERROR: missing $script — git pull origin main" >&2
    exit 1
  fi
  if [[ ! -x "$script" ]] && [[ "$script" == scripts/*.sh ]]; then
    chmod +x "$script" 2>/dev/null || true
  fi
  echo "  OK $script"
done

MINT_VERSION="$("$PY" -c "import integrations.mint_worker as m; print(m.__version__)" 2>/dev/null || echo unknown)"
echo "==> mint_worker package version: $MINT_VERSION"

OPTIONAL_CHECKS=(
  docs/standards/TP-108-AI-ATTESTATION.md
  ai_attestation_spec/zeegate_stub.py
)
echo "==> TP-108 (optional lab)"
for path in "${OPTIONAL_CHECKS[@]}"; do
  if [[ -f "$path" ]]; then
    echo "  OK $path"
  else
    echo "  WARN missing $path — git pull origin main"
  fi
done

MINT_URL="${MINT_WORKER_URL:-http://127.0.0.1:8090}"
if curl -sf "${MINT_URL}/health" >/dev/null 2>&1; then
  echo "==> Mint worker ${MINT_URL}/health"
  curl -sf "${MINT_URL}/health" | "$PY" -m json.tool | \
    grep -E '"status"|mint_worker_version|identity_mode|bearer_required|features' || true
else
  echo "SKIP: mint worker not running on ${MINT_URL}"
  echo "  Lab: ./scripts/start-mint-worker.sh"
  echo "  Staging: export MINT_WORKER_BEARER_TOKEN=... && ./scripts/restart-mint-worker-prod.sh"
fi

echo
echo "Replit sync check complete"
