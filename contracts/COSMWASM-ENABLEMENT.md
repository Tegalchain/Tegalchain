# CosmWasm enablement on cosmos-chain (SDK 0.53)

**Status (TP-104):** `tx-tel` CosmWasm contract is implemented and unit-tested.
`x/wasm` is **wired into `cosmos-chain`** via post-`Build` `RegisterStores` / `RegisterModules`
(wasmd **v0.61.7**, wasmvm **v3.0.2**) **without IBC**. Track B `x/gretelemetry` remains on
depinject and is unchanged.

## What landed

| Piece | Detail |
|-------|--------|
| Dependency | `github.com/CosmWasm/wasmd@v0.61.7` in `cosmos-chain/go.mod` |
| App wiring | `cosmos-chain/app/wasm.go` — nil IBC keepers; store/instantiate/execute for lab |
| Module order | `wasm` in Begin/End/InitGenesis lists in `app_config.go` (after gretelemetry where applicable) |
| CLI | `chaind query wasm` / `chaind tx wasm` (manual CLI attach; not depinject autocli) |
| Mint bridge | `integrations/tx_tel_mint` broadcasts `ExecuteMsg::Mint` when `TX_TEL_CONTRACT` is set **and** `chaind query wasm params` succeeds |

## Build / serve

wasmd needs **CGO** and `libwasmvm` (pulled via `github.com/CosmWasm/wasmvm/v3`).

```bash
# From sovereign-ecosystem
export CGO_ENABLED=1
# Optional on WSL without apt gcc — zig cc wrapper:
# export CC="$HOME/.local/bin/cc"
./scripts/start-cosmos-chain.sh build
./scripts/start-cosmos-chain.sh serve
```

Verify:

```bash
chaind query wasm params
chaind query gretelemetry params   # Track B must still work
```

**Genesis note:** adding the `wasm` store requires a **fresh** chain home (or migrator).
`ignite chain serve` recreates local genesis; do not expect an old `~/.chain` without wasm state
to start cleanly after this bump.

## Store / instantiate tx-tel

```bash
cd tegalchain-core/contracts
./scripts/install-rust.sh   # if needed
# Prefer Rust 1.86.x for wasmvm v3 bulk-memory compatibility (see wasmd#2316)
make build                  # or: cargo build --release --target wasm32-unknown-unknown -p tx-tel
./scripts/deploy-contracts.sh
export TX_TEL_CONTRACT=tegal1...
```

Then mint from a drained GTR:

```bash
# from sovereign-ecosystem
python3 -m integrations.tx_tel_mint <gtr_id>
# or
./scripts/phase7-tx-tel-mint-proof.sh <gtr_id>
```

## Why not Ignite `wasm add` / full IBC

| Factor | Detail |
|--------|--------|
| Ignite wasm app | Requires `app/ibc.go` + IBC stack; this chain has no IBC scaffold |
| wasmd DI | No `ProvideModule` for SDK 0.53 depinject — post-Build registration is the safe path |
| Risk | Pulling ibc-go + capability for lab mints would enlarge the blast radius around gretelemetry |

## Remaining blockers / follow-ups

1. **IBC (optional):** Full CosmWasm IBC (ICS-20, ICA callbacks) needs `ignite` IBC scaffold or manual ibc-go wiring, then Ignite wasm ante/IBC stack.
2. **Gov authority:** Wasm authority is `authtypes.NewModuleAddress("gov")` but `x/gov` is not scaffolded — param updates via gov proposals are not available yet.
3. **Ante / snapshots:** Lab wiring skips wasmd `CountTXDecorator` and wasm snapshotter; add before production load.
4. **Contract toolchain:** Build `tx-tel` with Rust **≤ 1.86** (or a wasmvm that supports newer bulk-memory) before `tx wasm store`.
5. **Parent pointer:** After merging `tegalchain-core`, bump the submodule SHA in sovereign-ecosystem.

## Non-goals

- Do not couple Zeegate / Bytenergy to wasmd — mint remains oracle-mediated.
- Do not replace `x/gretelemetry` anchors with contract calls.
