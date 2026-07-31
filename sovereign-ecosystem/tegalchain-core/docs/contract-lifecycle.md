# Contract lifecycle

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#contract-lifecycle](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#contract-lifecycle).

Smart contract deployment and upgrade follow a **governed multi-org lifecycle** so no single organisation can unilaterally change shared channel state.

## Phases

| Phase | Description |
|-------|-------------|
| **Package** | Compile and package the contract into a deployment archive (CosmWasm `.wasm`) |
| **Install** | Install the package on peers of each organisation that will run it |
| **Approve** | Each org admin approves the definition — including **endorsement policy** |
| **Commit** | After enough org approvals, the definition is committed to the channel and becomes **active** |

```text
Package → Install → Approve → Commit → Active on channel
```

## Distinction from transaction flow

- **Contract lifecycle** — governs **what code and policies** exist on the channel  
- **Transaction flow** — governs **invocations** of an already-active contract  

See also [endorsement-policies.md](./endorsement-policies.md) · [transaction-flow.md](./transaction-flow.md) · [contract-interface.md](./contract-interface.md) · [cosmos-wasm-architecture.md](./cosmos-wasm-architecture.md).

## Phase 1 (Greenledger)

The Python gretelemetry bridge does not run contract lifecycle steps. CosmWasm packaging exists under `contracts/`; full Install → Approve → Commit is a **target** on the Cosmos channel.
