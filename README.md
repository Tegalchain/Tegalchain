# Tegalchain

## What is Tegalchain?

Tegalchain is a **permissioned distributed ledger protocol** designed for high-throughput, auditable record-keeping across multi-party networks. Unlike public blockchain networks optimised for open participation, Tegalchain prioritises **deterministic finality**, **regulatory compliance**, and **fine-grained access control** — making it well-suited for institutional, governmental, and enterprise deployments.

## At its core

- A **shared, tamper-evident ledger** accessible to all permissioned participants
- A **smart contract runtime** for encoding business logic on-chain (CosmWasm — see `docs/cosmos-wasm-architecture.md`)
- An **on-chain governance** system for protocol upgrades and network-wide decisions (see `GOVERNANCE.md`, sovereign-ecosystem [TEGAL-TOKENS.md](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/contracts/TEGAL-TOKENS.md))
- A **pluggable consensus layer** supporting multiple Byzantine Fault Tolerant (BFT) algorithms (Cosmos SDK target; PoREF handles evidence-layer validator consensus)

**Transactions:** the atomic unit of ledger change (sender, payload, nonce, signature, timestamp) — see [docs/transactions.md](./docs/transactions.md). **Blocks:** ordered transaction bundles from the ordering service — see [docs/blocks.md](./docs/blocks.md). **Lifecycle:** proposal → endorse → order → commit — see [docs/transaction-flow.md](./docs/transaction-flow.md). **Endorsement policies:** per-contract org expressions (`AND`, `OR`, `OutOf`) — see [docs/endorsement-policies.md](./docs/endorsement-policies.md). **Contract lifecycle:** governed Package → Install → Approve → Commit — see [docs/contract-lifecycle.md](./docs/contract-lifecycle.md). **Contract interface:** named invoke/query functions with transaction context — see [docs/contract-interface.md](./docs/contract-interface.md). **Contract best practices:** deterministic, validated, idempotent design — see [docs/contract-best-practices.md](./docs/contract-best-practices.md). **Client applications:** off-chain SDK for propose → endorse → order → query — see [docs/client-applications.md](./docs/client-applications.md). **State database:** LevelDB or CouchDB peer KV store — see [docs/state-database.md](./docs/state-database.md). **State access:** contract `ctx.state` API — see [docs/state-access-patterns.md](./docs/state-access-patterns.md). **Network configuration:** channel config block — see [docs/network-configuration.md](./docs/network-configuration.md). **Protocol upgrades:** capability flags — see [docs/protocol-upgrades.md](./docs/protocol-upgrades.md). **Access control lists:** system API ACLs — see [docs/access-control-lists.md](./docs/access-control-lists.md). **Finality:** deterministic irreversible commit — see [docs/finality.md](./docs/finality.md). **Gossip:** restricted P2P data plane after ordering — see [docs/gossip.md](./docs/gossip.md).

## Protocol stack

**TP-101** GreenTelemetry → **TP-102** Proof of Resonance → **TP-103** GreenLedger → **TP-104** Transynth → **TP-105** Voixcoin → **TP-106** TEGAL DAO → **TP-107** Sovereign Platforms — see [docs/protocol-stack.md](./docs/protocol-stack.md).

## Greenledger application (Proof of Resonance)

This repository also implements the **Greenledger** (**TP-103**) — an environmental and provenance layer on Tegalchain using the Proof of Resonance (**TP-102**) stack:

- **PoRE** — Proof of Resonance Evidence  
- **PoREF** — Proof of Resonance Foundation  
- **PoREX** — Proof of Resonance Exchange  

The platform uses a Cosmos SDK-based chain with CosmWasm smart contracts (Rust), Go services for consensus, and Python services for real-time telemetry and analytics. The [sovereign-ecosystem](https://github.com/Shootle/sovereign-ecosystem) monorepo connects DePIN/utility producers via the **gretelemetry oracle**.

Goals
- Enable tokenized impact via **Transitional Synthetic Assets (Transynths)** — digitally represented as **tX***, where * indexes environmentally provenance asset types — backed by verifiable resonance evidence.
- Require green energy and verified environmental attributes for block creation.
- Provide auditable, permissioned governance (TEGAL/uteg, DAO policy) over institutional-grade record-keeping.

Canonical overview (permissioned ledger + monorepo mapping): [sovereign-ecosystem/docs/TEGALCHAIN.md](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md)

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
