# Contracts Workspace

CosmWasm contracts for the Tegalchain PoR / PoREX stack. Each contract is a Rust crate under this workspace.

**Active member (TP-104 lab):** `tx-tel/` — tXtel telecom Transynth with GLE/PoRE mint gates.

Planned Transynth crates (not yet scaffolded):

| Token ID | Crate path | Description |
|----------|------------|-------------|
| **tXcarbon** | `tx-carbon/` | Carbon Transynth |
| **tXbiodiversity** | `tx-biodiversity/` | Biodiversity Transynth |
| **tXwater** | `tx-water/` | Water Transynth |
| **tXsoil** | `tx-soil/` | Soil Transynth |
| **tXIREC** | `tx-irec/` | I-REC Transynth |
| **tXenergy** | `tx-energy/` | Green energy production Transynth |
| **tXtel** | `tx-tel/` | Telecom provenance Transynth — **live crate** |

Shared infrastructure crates (planned): `token-factory/`, `por-evidence-registry/`, `poref-validation/`, `impact-market/`, `token-retirement/`, `validator-slashing/`, `reward-distribution/`.

## Setup

```bash
./scripts/install-rust.sh
make test
make build
```

## CosmWasm on cosmos-chain

See [COSMWASM-ENABLEMENT.md](./COSMWASM-ENABLEMENT.md). `x/wasm` is wired (no IBC). Deploy with `./scripts/deploy-contracts.sh`, then set `TX_TEL_CONTRACT` so the oracle mint bridge (`integrations/tx_tel_mint`) broadcasts `ExecuteMsg::Mint`. Without a contract address, the bridge still records off-chain intents.

See [DEVELOPMENT.md](./DEVELOPMENT.md) for conventions.
