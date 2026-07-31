# Transaction flow

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#transaction-flow](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#transaction-flow).

Five phases: **Proposal → Simulation → Endorsement collection → Ordering → Validation and commit**. Phases 1–3 are governed by the contract's **endorsement policy** — see [endorsement-policies.md](./endorsement-policies.md). **Client applications** drive phases 1–4 off-chain — see [client-applications.md](./client-applications.md). After ordering, **gossip** disseminates committed blocks to channel peers.

See also [transactions.md](./transactions.md) · [blocks.md](./blocks.md) · [gossip.md](./gossip.md) · [endorsement-policies.md](./endorsement-policies.md) · [client-applications.md](./client-applications.md).

Phase 1 gretelemetry uses the mint worker as a simplified endorsement edge before ordering on the chain node.
