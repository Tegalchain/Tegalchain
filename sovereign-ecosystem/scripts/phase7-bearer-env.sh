# shellcheck shell=bash
# Shared Bearer token checks for Phase 7 staging scripts (source, do not execute).
phase7_require_bearer_token() {
  local token="${MINT_WORKER_BEARER_TOKEN:-}"
  if [[ -z "$token" ]]; then
    echo "ERROR: MINT_WORKER_BEARER_TOKEN must be set (same value as prod worker Shell 1)" >&2
    echo "  Example: export MINT_WORKER_BEARER_TOKEN=\$(openssl rand -hex 24)" >&2
    return 1
  fi
  case "$token" in
    your-saved-token|your-actual-secret-here|paste-your-saved-token-here|same-secret)
      echo "ERROR: MINT_WORKER_BEARER_TOKEN is a documentation placeholder — use the real secret" >&2
      echo "  Must match the token exported when you ran restart-mint-worker-prod.sh in Shell 1" >&2
      return 1
      ;;
  esac
  if [[ "$token" == *'<'* ]]; then
    echo "ERROR: MINT_WORKER_BEARER_TOKEN looks like a doc placeholder (contains '<')" >&2
    return 1
  fi
  return 0
}
