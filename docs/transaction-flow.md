# Transaction flow

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#transaction-flow](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#transaction-flow).

Five phases: **Proposal → Simulation → Endorsement collection → Ordering → Validation and commit**. After ordering, **gossip** disseminates committed blocks to channel peers.

See also [transactions.md](./transactions.md) · [blocks.md](./blocks.md) · [gossip.md](./gossip.md).

Phase 1 gretelemetry uses the mint worker as a simplified endorsement edge before ordering on the chain node.
