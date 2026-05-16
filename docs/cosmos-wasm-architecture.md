# Cosmos Wasm Architecture

Tegalchain uses Cosmos SDK (Go) as the chain layer and CosmWasm (Rust) for smart contracts. Key points:

- Contracts are authored in Rust and compiled to Wasm. Use `wasm32-unknown-unknown` target.
- Contracts expose instantiate, execute, and query handlers and follow CosmWasm best practices.
- IBC support is enabled for cross-chain token bridging of tX*.
- Contracts interact with Go modules via standard message passing and indexed events.

Development
- Use `cargo wasm`, `cargo test` and `cosmwasm-optimize` as part of the build pipeline.
- Contracts are organized under `contracts/` as an integrated workspace.
