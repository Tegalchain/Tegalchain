#!/usr/bin/env bash
# Phase 3 — generate a lab CDR row inside FreeSWITCH (no external softphone required).
#
# Runs an internal originate to extension 1000 (echo) with caller edge001 so the
# CDR adapter maps tegalid correctly. Use when Replit blocks UDP SIP/RTP.
#
# Prerequisites: zeegate-freeswitch container Up (./up.sh)
# Then: ./scripts/phase3-fs-lab-call.sh && ./scripts/phase3-live-cdr.sh drain
set -euo pipefail

CONTAINER="${ZEEGATE_FS_CONTAINER:-zeegate-freeswitch}"
FS_CLI_HOST="${ZEEGATE_FS_CLI_HOST:-127.0.0.1}"
FS_CLI_PORT="${ZEEGATE_FS_CLI_PORT:-8021}"
FS_CLI_PASS="${ZEEGATE_FS_CLI_PASS:-ClueCon}"

fs_cli() {
  docker exec "$CONTAINER" fs_cli -H "$FS_CLI_HOST" -P "$FS_CLI_PORT" -p "$FS_CLI_PASS" "$@"
}

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "ERROR: container '$CONTAINER' not running. cd zeegate-cloud/deploy && ./up.sh" >&2
  exit 1
fi

if ! fs_cli -x "status" 2>/dev/null | grep -q "UP"; then
  echo "ERROR: fs_cli cannot reach FreeSWITCH ESL at ${FS_CLI_HOST}:${FS_CLI_PORT}" >&2
  echo "  Ensure event_socket.conf.xml is mounted (git pull) and recreate FreeSWITCH:" >&2
  echo "  cd zeegate-cloud/deploy && docker compose up -d --force-recreate freeswitch" >&2
  fs_cli -x "status" 2>&1 || true
  exit 1
fi

echo "==> Originating lab echo call (caller edge001 → 1000) in $CONTAINER"
fs_cli -x \
  "originate {origination_caller_id_number=edge001,origination_caller_id_name=edge001}loopback/1000/public &echo()"

echo "==> Done. Wait for hangup CDR flush, then sync:"
echo "    ./scripts/phase3-live-cdr.sh inspect"
echo "    ./scripts/phase3-live-cdr.sh drain"
