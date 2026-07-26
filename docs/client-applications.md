# Client applications

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#client-applications](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#client-applications).

Off-chain **client applications** interact with the permissioned network through the **Tegalchain SDK**. Clients:

1. Construct and sign transaction proposals  
2. Submit proposals to peers for endorsement  
3. Submit endorsed transactions to the ordering service  
4. Query ledger state via peer read operations  

## Client vs peer

| Component | Role |
|-----------|------|
| **Client** | Off-chain; drives proposal → endorse → order; holds user/org keys |
| **Peer** | On-channel; simulates, endorses, orders, commits, serves queries |

## SDK surface (target)

Identity/signing, contract invoke/query serialization, endorsement collection, ordering submission, commit event subscription.

## Phase 1 (Greenledger)

Responsibilities are split today:

| Role | Component |
|------|-----------|
| Producer client | `integrations/zeegate_telemetry`, `bytenergy-utility`, Android GreTelemetry |
| Endorsement edge | `integrations/mint_worker` |
| Ordering client | `tegalchain/submitter` |

Unified SDK consolidates these paths on the Cosmos target.

See also [transaction-flow.md](./transaction-flow.md) · [contract-interface.md](./contract-interface.md) · [endorsement-policies.md](./endorsement-policies.md).
