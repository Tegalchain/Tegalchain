#!/usr/bin/env bash
# Store + instantiate tx-tel on a wasmd-enabled cosmos-chain.
#
# Prerequisites:
#   1. wasmd module enabled on chain (see contracts/COSMWASM-ENABLEMENT.md)
#   2. Optimized (or cargo) wasm artifact at artifacts/tx_tel.wasm or tx-tel/target/...
#   3. chaind on PATH, funded key (default alice / test keyring)
#
# Usage:
#   ./scripts/deploy-contracts.sh
#   TX_TEL_MINTER=$(chaind keys show alice -a --keyring-backend test) ./scripts/deploy-contracts.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.cargo/bin:${HOME}/go/bin:${HOME}/gopath/bin:${PATH:-}"

CHAIND="${COSMOS_CHAIND:-chaind}"
FROM="${COSMOS_CHAIND_FROM:-alice}"
KEYRING="${COSMOS_CHAIND_KEYRING:-test}"
NODE="${COSMOS_CHAIND_NODE:-tcp://127.0.0.1:26657}"
CHAIN_ID="${COSMOS_CHAIND_CHAIN_ID:-chain}"
FEES="${TX_TEL_FEES:-0stake}"

if ! command -v "$CHAIND" >/dev/null 2>&1; then
  echo "ERROR: $CHAIND not on PATH — build cosmos-chain first" >&2
  exit 1
fi

# Detect wasm module
if ! "$CHAIND" query wasm params --node "$NODE" >/dev/null 2>&1; then
  echo "ERROR: chaind has no wasm query — wasmd not enabled yet." >&2
  echo "  See contracts/COSMWASM-ENABLEMENT.md" >&2
  echo "  Until then, use off-chain mint intents:" >&2
  echo "    python -m integrations.tx_tel_mint <gtr_id>" >&2
  exit 2
fi

WASM=""
for candidate in \
  "$ROOT/artifacts/tx_tel.wasm" \
  "$ROOT/target/wasm32-unknown-unknown/release/tx_tel.wasm" \
  "$ROOT/tx-tel/target/wasm32-unknown-unknown/release/tx_tel.wasm"; do
  if [[ -f "$candidate" ]]; then
    WASM="$candidate"
    break
  fi
done

if [[ -z "$WASM" ]]; then
  echo "==> Building tx-tel wasm"
  (cd "$ROOT" && CARGO_TARGET_DIR="$ROOT/target" cargo build --release --target wasm32-unknown-unknown -p tx-tel)
  WASM="$ROOT/target/wasm32-unknown-unknown/release/tx_tel.wasm"
fi

MINTER="${TX_TEL_MINTER:-$("$CHAIND" keys show "$FROM" -a --keyring-backend "$KEYRING")}"
INIT_MSG=$(cat <<EOF
{"minter":"$MINTER","admin":null,"min_eqs":null,"min_riv_exclusive":null,"min_consensus_confidence":null,"min_resonance_score":null}
EOF
)

echo "==> Storing $WASM"
STORE_OUT=$("$CHAIND" tx wasm store "$WASM" \
  --from "$FROM" --keyring-backend "$KEYRING" \
  --node "$NODE" --chain-id "$CHAIN_ID" \
  --gas auto --gas-adjustment 1.4 --fees "$FEES" \
  --yes --output json)
TXHASH=$(echo "$STORE_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('txhash',''))")
echo "store txhash: $TXHASH"
sleep 6

CODE_ID=$("$CHAIND" query tx "$TXHASH" --node "$NODE" -o json \
  | python3 -c "
import sys, json
tx = json.load(sys.stdin)
for e in tx.get('events', []):
  if e.get('type') == 'store_code':
    for a in e.get('attributes', []):
      if a.get('key') in ('code_id', 'codeID'):
        print(a['value']); raise SystemExit
print('', end='')
")

if [[ -z "$CODE_ID" ]]; then
  echo "ERROR: could not resolve code_id from store tx" >&2
  exit 1
fi
echo "==> code_id=$CODE_ID"

echo "==> Instantiating tx-tel (minter=$MINTER)"
INST_OUT=$("$CHAIND" tx wasm instantiate "$CODE_ID" "$INIT_MSG" \
  --label "tx-tel" --admin "$MINTER" \
  --from "$FROM" --keyring-backend "$KEYRING" \
  --node "$NODE" --chain-id "$CHAIN_ID" \
  --gas auto --gas-adjustment 1.4 --fees "$FEES" \
  --yes --output json)
INST_HASH=$(echo "$INST_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('txhash',''))")
echo "instantiate txhash: $INST_HASH"
sleep 6

CONTRACT=$("$CHAIND" query tx "$INST_HASH" --node "$NODE" -o json \
  | python3 -c "
import sys, json
tx = json.load(sys.stdin)
for e in tx.get('events', []):
  if e.get('type') in ('instantiate', 'wasm'):
    for a in e.get('attributes', []):
      if a.get('key') in ('_contract_address', 'contract_address'):
        print(a['value']); raise SystemExit
print('', end='')
")

if [[ -z "$CONTRACT" ]]; then
  echo "ERROR: could not resolve contract address" >&2
  exit 1
fi

echo "OK: TX_TEL_CONTRACT=$CONTRACT"
echo "export TX_TEL_CONTRACT=$CONTRACT"
echo "Then: python -m integrations.tx_tel_mint <gtr_id>"
