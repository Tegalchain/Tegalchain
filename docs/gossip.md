# Gossip protocol

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#gossip-protocol-data-plane](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#gossip-protocol-data-plane).

**Restricted gossip** complements the **ordering service**: it propagates committed blocks, state deltas, and peer metadata across permissioned channel peers without a central data coordinator.

Gossip does **not** replace BFT ordering, endorsement policy, or the gretelemetry oracle ingress.

## Planes

| Plane | Component |
|-------|-----------|
| Consensus | Ordering service + BFT |
| Data | Gossip protocol |
| Ingress | Gretelemetry oracle (sovereign-ecosystem) |

## Target implementation

- CometBFT / Cosmos SDK P2P block and state sync among validators  
- Channel-bound, authenticated gossip for commit peers  
- No gossip of raw edge telemetry — only committed ledger artifacts  

See also [blocks.md](./blocks.md) · [transaction-flow.md](./transaction-flow.md).
