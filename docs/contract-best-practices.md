# Contract best practices

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#contract-best-practices](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#contract-best-practices).

Tegalchain contracts must produce **identical simulation results** on every endorsing peer. Follow these rules when authoring CosmWasm modules:

| Practice | Rationale |
|----------|-----------|
| **Keep contracts small and focused** | One contract per business domain |
| **Validate all inputs** | Never trust client-supplied data |
| **Use deterministic operations only** | Avoid RNG, external API calls, or time-sensitive logic that diverges across peers |
| **Write idempotently where possible** | Safe retries simplify client and outbox error handling |

## Determinism

Endorsers simulate independently. Non-deterministic invokes produce mismatched read/write sets and break ordering.

**Avoid:** random numbers, HTTP oracles, wall-clock business logic inside invoke.  
**Prefer:** arguments from endorsed upstream txs, committed ledger state, block height / tx timestamp from runtime metadata.

## Idempotency

Use explicit keys (`create_if_absent`, state-guarded transitions, dedupe hashes) so duplicate submissions fail cleanly rather than corrupt state.

See also [contract-interface.md](./contract-interface.md) · [transaction-flow.md](./transaction-flow.md) · [cosmos-wasm-architecture.md](./cosmos-wasm-architecture.md).
