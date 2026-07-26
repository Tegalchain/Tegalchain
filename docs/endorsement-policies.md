# Endorsement policies

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#endorsement-policies](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#endorsement-policies).

Before a transaction reaches the **ordering service**, it must satisfy the **endorsement policy** for the target smart contract — rules specifying which peers must sign the transaction's **read/write set**.

## Expression syntax

Policies are **logical expressions over organisations**:

```python
AND('OrgA.peer', 'OrgB.peer')                              # Both OrgA and OrgB must endorse
OR('OrgA.peer', 'OrgB.peer')                               # Either OrgA or OrgB must endorse
OutOf(2, 'OrgA.peer', 'OrgB.peer', 'OrgC.peer')            # Any 2 of 3 must endorse
```

## Scope

- Set **per smart contract** (CosmWasm instance on target runtime)
- Updatable through **on-chain governance**
- Verified again at **validation and commit** by all channel peers

## Phase 1 (Greenledger)

Gretelemetry uses a **simplified single-oracle gate** (mint worker) instead of a full multi-org policy evaluator. Full `AND` / `OR` / `OutOf` evaluation is a **target** on the Cosmos channel.

See also [transaction-flow.md](./transaction-flow.md) · [transactions.md](./transactions.md).
