#!/usr/bin/env bash
# Verify whether Redis is configured or running in a Replit Tegalchain environment.
# Run inside Replit Shell:
#   curl -fsSL https://raw.githubusercontent.com/Shootle/sovereign-ecosystem/main/scripts/replit-verify-redis.sh | bash
# Or after git pull:
#   bash scripts/replit-verify-redis.sh
set -u

PASS=0
WARN=0
FAIL=0

ok()   { echo "  [ok]   $*"; PASS=$((PASS + 1)); }
warn() { echo "  [warn] $*"; WARN=$((WARN + 1)); }
bad()  { echo "  [no]   $*"; FAIL=$((FAIL + 1)); }

section() { echo; echo "== $* =="; }

section "Environment"
for var in REDIS_URL REDIS_HOST REDIS_PORT REDIS_PASSWORD REDIS_TLS_URL; do
  if [[ -n "${!var:-}" ]]; then
    ok "$var is set"
  else
    bad "$var is unset"
  fi
done

section "Replit config files"
for f in .replit replit.nix replit.toml .replit.nix; do
  if [[ -f "$f" ]]; then
    ok "found $f"
    if rg -i 'redis' "$f" >/dev/null 2>&1; then
      warn "$f mentions redis:"
      rg -n -i 'redis' "$f" | sed 's/^/         /'
    else
      bad "$f has no redis reference"
    fi
  else
    bad "missing $f"
  fi
done

section "Running services"
if command -v redis-cli >/dev/null 2>&1; then
  ok "redis-cli installed: $(command -v redis-cli)"
else
  bad "redis-cli not installed"
fi

if pgrep -a redis-server >/dev/null 2>&1; then
  ok "redis-server process running"
  pgrep -a redis-server | sed 's/^/         /'
else
  bad "redis-server process not running"
fi

if command -v ss >/dev/null 2>&1; then
  if ss -ltn 2>/dev/null | rg -q ':6379'; then
    ok "TCP port 6379 is listening"
  else
    bad "TCP port 6379 is not listening"
  fi
elif command -v netstat >/dev/null 2>&1; then
  if netstat -ltn 2>/dev/null | rg -q ':6379'; then
    ok "TCP port 6379 is listening"
  else
    bad "TCP port 6379 is not listening"
  fi
else
  warn "cannot check port 6379 (no ss/netstat)"
fi

if command -v redis-cli >/dev/null 2>&1; then
  if redis-cli ping 2>/dev/null | rg -qi '^PONG'; then
    ok "redis-cli ping → PONG"
  else
    bad "redis-cli ping failed"
  fi
fi

section "Repo / build references"
if [[ -f go.mod ]]; then
  ok "found go.mod"
  if rg -i 'redis' go.mod go.sum 2>/dev/null; then
    warn "Go module lists redis (may be transitive only)"
  else
    bad "go.mod/go.sum has no redis dependency"
  fi
else
  bad "no go.mod in $(pwd)"
fi

if [[ -f qortal/pom.xml ]]; then
  if rg -i 'redis' qortal/pom.xml >/dev/null 2>&1; then
    warn "qortal/pom.xml mentions redis"
  else
    bad "qortal/pom.xml has no redis dependency (uses HSQLDB instead)"
  fi
fi

if ls Tegalchain_Blockchain_Genesis*.ipynb >/dev/null 2>&1; then
  if rg -l -i 'go-redis|miniredis|cloud.google.com/go/redis' Tegalchain_Blockchain_Genesis*.ipynb >/dev/null 2>&1; then
    warn "Genesis notebook output includes transitive Go redis modules (not a live Redis service)"
  fi
fi

section "Summary"
echo "  pass=$PASS  warn=$WARN  no=$FAIL"
echo
if [[ "$PASS" -gt 0 && "$FAIL" -gt 0 ]]; then
  echo "Redis is NOT fully rendered in this Replit build."
  echo "Any redis mentions in Go notebooks are likely transitive module listings only."
elif [[ "$FAIL" -eq 0 && "$PASS" -gt 0 ]]; then
  echo "Redis appears configured on this Repl."
else
  echo "Redis does not appear to be part of this Replit environment."
fi
