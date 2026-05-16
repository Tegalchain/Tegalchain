# Development — Contracts

Setup
1. Install Rust (stable) and add target: `rustup target add wasm32-unknown-unknown`.
2. Install `cargo-generate`, `wasm-bindgen-cli` if needed, and CosmWasm tooling.
3. From `contracts/` run `make build` to compile wasm artifacts.

Testing
- Run `make test` to execute Rust unit tests for each contract crate.

Best practices
- Keep instantiate/execute/query interfaces minimal.
- Use structured messages and version contracts.
- Include thorough unit and integration tests.
