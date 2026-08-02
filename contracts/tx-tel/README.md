# tx-tel — tXtel CosmWasm contract (TP-104)

Telecom provenance Transynth. Mints **tXtel** when an authorized oracle minter submits RFM fields that pass PoREX lab gates (TP-102):

| Gate | Lab default |
|------|-------------|
| EQS | ≥ 0.70 |
| RIV | > 0 |
| Consensus Confidence | ≥ 1.0 |
| Evidence Resonance | ≥ 50 |

One mint per `gtr_id`. Stores `gtr_hash` for GLE correlation.

## Build / test

```bash
# from contracts/
../contracts/scripts/install-rust.sh   # or ./scripts/install-rust.sh
cargo test -p tx-tel
cargo build --release --target wasm32-unknown-unknown -p tx-tel
```

## Deploy

Requires wasmd on cosmos-chain — see [../COSMWASM-ENABLEMENT.md](../COSMWASM-ENABLEMENT.md) and `../scripts/deploy-contracts.sh`.
