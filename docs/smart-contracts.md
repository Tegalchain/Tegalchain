# Smart Contracts (CosmWasm) — Overview

Contracts in this workspace implement PoR registry, validator consensus helpers, token factory, tX* tokens, market primitives (AMM/orderbook), retirement and reward distribution. Each contract is a separate Rust crate in the `contracts/` workspace.

Security
- Use unit tests and integration tests. Aim for high coverage and consider formal verification for core contracts (registry, token factory, retirement).
- Use multi-sig patterns for validator-critical operations.
