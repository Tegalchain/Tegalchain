# CosmWasm enablement on cosmos-chain (SDK 0.53)

**Status (TP-104 slice):** `tx-tel` CosmWasm contract is **implemented and unit-tested**. On-chain `x/wasm` is **not yet wired** into the Ignite-scaffolded `cosmos-chain` app — Track B `x/gretelemetry` anchor path stays unchanged.

## Why not wasmd in this slice

| Factor | Detail |
|--------|--------|
| App wiring | Ignite depinject `app_config.go` — adding wasmd requires module config, keepers, genesis, and often IBC/capability deps |
| Compatibility | Prefer **wasmd ≥ v0.60.1 / v0.61.x** for Cosmos SDK **v0.53.x** (see [wasmd CHANGELOG](https://github.com/CosmWasm/wasmd/blob/main/CHANGELOG.md)) |
| Risk | Full integration can break the proven Phase 5 / Track B gretelemetry drain until carefully validated |

Until wasmd lands, the lab path is:

1. Build + unit-test `tx-tel` (this workspace).
2. Record mint intents via the oracle-side bridge (`integrations/tx_tel_mint` in sovereign-ecosystem) after GLE + PoRE gates pass.
3. After wasmd is enabled: `contracts/scripts/deploy-contracts.sh` → set `TX_TEL_CONTRACT` → bridge broadcasts `ExecuteMsg::Mint`.

## Recommended enablement steps

1. Add dependency (pin to a wasmd release matching SDK 0.53.6):

   ```bash
   cd cosmos-chain
   go get github.com/CosmWasm/wasmd@v0.61.7   # or latest 0.61.x / 0.60.1+
   go mod tidy
   ```

2. Wire `x/wasm` into `app/app_config.go` (BeginBlockers / EndBlockers / InitGenesis) and `app/app.go` keepers per [wasmd INTEGRATION.md](https://github.com/CosmWasm/wasmd/blob/main/INTEGRATION.md). Prefer copying the minimal `x/wasm` wiring from a wasmd demo app of the same SDK minor.

3. Ensure `libwasmvm` matches the wasmd/wasmvm module version (CGO). Rebuild:

   ```bash
   ./scripts/start-cosmos-chain.sh build   # from sovereign-ecosystem
   ```

4. Verify:

   ```bash
   chaind query wasm params
   ```

5. Deploy tXtel:

   ```bash
   cd tegalchain-core/contracts
   ./scripts/install-rust.sh
   make build
   ./scripts/deploy-contracts.sh
   export TX_TEL_CONTRACT=tegal1...
   ```

6. Prove one mint from a drained GTR (see Phase 7 runbook in sovereign-ecosystem).

## Non-goals for this doc

- Do not couple Zeegate / Bytenergy to wasmd — mint remains oracle-mediated.
- Do not replace `x/gretelemetry` anchors with contract calls.
