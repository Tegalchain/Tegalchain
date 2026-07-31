#!/usr/bin/env bash
# Ensure Python deps for Replit (Nix/PEP 668) and local lab.
# Usage: source scripts/replit-ensure-deps.sh
# Sets REPLIT_PY to the python interpreter with deps available.
set -euo pipefail

_replit_root="${REPLIT_REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$_replit_root"

if command -v python3 >/dev/null 2>&1; then
  REPLIT_PY=python3
else
  REPLIT_PY=python
fi

_replit_deps_ok() {
  "$REPLIT_PY" -c "import fastapi, uvicorn, jsonschema, cryptography" >/dev/null 2>&1
}

if _replit_deps_ok; then
  echo "OK: Python deps already importable ($("$REPLIT_PY" --version))"
  export REPLIT_PY
  return 0 2>/dev/null || exit 0
fi

echo "==> Installing Python deps for $("$REPLIT_PY" --version)..."

if "$REPLIT_PY" -m pip install -q -r requirements.txt 2>/dev/null; then
  export REPLIT_PY
  return 0 2>/dev/null || exit 0
fi

echo "WARN: system pip blocked (Nix/PEP 668) — using project .venv"
if [[ ! -d .venv ]]; then
  "$REPLIT_PY" -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
REPLIT_PY=python
pip install -q -r requirements.txt
export REPLIT_PY
echo "OK: deps installed in .venv — use: source .venv/bin/activate"
