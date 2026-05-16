# Tegalchain

Tegalchain is a regenerative finance platform implementing the Proof of Resonance (PoR) Stack: PoRE (Proof of Regenerative Evidence), PoREF (Proof of Resonance Foundation) and PoREX (Proof of Resonance Exchange). The platform uses a Cosmos SDK-based chain with CosmWasm smart contracts (Rust), Go services for consensus, and Python services for real-time telemetry and analytics.

Goals
- Enable tokenized impact (tX* synthetic tokens) backed by verifiable regenerative evidence.
- Require green energy and verified environmental attributes for block creation.
- Provide open, auditable, and community-driven DAO governance.

Quick start
1. Install dependencies: Go, Rust (with wasm32-unknown-unknown target), Cargo, Node (for tooling), Python 3.10+, Docker.
2. Build contracts: `make -C contracts build`
3. Start local testnet: see `contracts/DEVELOPMENT.md` and `docs/cosmos-wasm-architecture.md` for examples.

Repository layout
- contracts/        : CosmWasm (Rust) contracts workspace
- docs/             : Architecture, PoR stack, tokenomics, telemetry integration
- .github/          : Issue and PR templates
- README.md, CONTRIBUTING.md, GOVERNANCE.md, CODE_OF_CONDUCT.md

If you're new, read CONTRIBUTING.md to get started with development and the PoR contribution pathways.
