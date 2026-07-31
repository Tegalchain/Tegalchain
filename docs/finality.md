# Finality

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#finality](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#finality).

Tegalchain provides **deterministic finality**: once a transaction is in a **committed block**, it is **irreversible**.

- No fork risk after BFT commit  
- No probabilistic finality  
- No confirmation depth  

Finality is reached at **validation and commit** (phase 5). Gossip then propagates the final block to all peers.

## Phase 1 (Greenledger)

Application-observed finality: mint queue `status=submitted` with chain `submit_ref`. See `tegalchain/finality.py` in sovereign-ecosystem.

See also [transaction-flow.md](./transaction-flow.md) · [blocks.md](./blocks.md) · [gossip.md](./gossip.md).
