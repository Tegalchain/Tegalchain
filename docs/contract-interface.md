# Contract interface

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#contract-interface](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#contract-interface).

A Tegalchain smart contract exposes **named functions** for client **invoke** (state-changing) and **query** (read-only) operations.

## Function inputs

| Input | Role |
|-------|------|
| **Transaction context** (`ctx`) | Ledger state, transaction metadata, caller identity |
| **Arguments** | Client-supplied parameters |

## Transaction context

| Member | Role |
|--------|------|
| `ctx.state` | Contract-scoped key-value state (`get`, `put`, `exists`) |
| `ctx.identity` | Permissioned caller identity |

**Invoke** functions mutate state and follow the full [transaction-flow.md](./transaction-flow.md). **Query** functions are read-only.

## CosmWasm mapping (target)

| Pseudocode | CosmWasm |
|------------|----------|
| Invoke | `execute` messages |
| Query | `query` messages |
| `ctx.state` | `deps.storage` |
| `ctx.identity` | `info.sender` (+ tegalid-bound addresses) |

See also [contract-lifecycle.md](./contract-lifecycle.md) · [endorsement-policies.md](./endorsement-policies.md) · [contract-best-practices.md](./contract-best-practices.md) · [state-access-patterns.md](./state-access-patterns.md) · [cosmos-wasm-architecture.md](./cosmos-wasm-architecture.md).

## Phase 1 (Greenledger)

Gretelemetry ingress uses the Python oracle bridge (`TELEMETRY_MINT`), not direct contract invokes. CosmWasm contracts under `contracts/` define the target invoke/query surface for Transynths, Voixcoin, and PoREX.
