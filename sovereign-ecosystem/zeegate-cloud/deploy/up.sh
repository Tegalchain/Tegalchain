#!/usr/bin/env bash
# Phase 2 lab — start Kamailio + FreeSWITCH voice stack.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/deploy"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created deploy/.env from .env.example"
fi

docker compose up -d "$@"
docker compose ps

echo ""
echo "SIP registrar: udp://$(hostname -I 2>/dev/null | awk '{print $1}'):5060  domain=zeegate.lab"
echo "Lab accounts: edge001/edge001 (Zeegate), lab1000/lab1000 (softphone)"
echo "Media extensions via Kamailio: 1000=echo, 2000=tone, 3000=bridge edge001"
