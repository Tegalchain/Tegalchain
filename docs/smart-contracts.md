# Smart Contracts (CosmWasm) — Overview

Contracts in this workspace implement PoR registry, validator consensus helpers, token factory, Transynths (tX*), market primitives (AMM/orderbook), retirement and reward distribution. Each contract is a separate Rust crate in the `contracts/` workspace.

## Active: tx-tel (TP-104)

- Path: `contracts/tx-tel/`
- Token: **tXtel** (telecom provenance)
- Mint gates (lab): EQS ≥ 0.70, RIV > 0, consensus confidence ≥ 1.0, evidence resonance ≥ 50
- Minter: admin-configured oracle address (`ExecuteMsg::Mint`)
- wasmd on `cosmos-chain`: see `contracts/COSMWASM-ENABLEMENT.md`

```bash
cd contracts && ./scripts/install-rust.sh && make test && make build
```

Security
- Use unit tests and integration tests. Aim for high coverage and consider formal verification for core contracts (registry, token factory, retirement).
- Use multi-sig patterns for validator-critical operations.
