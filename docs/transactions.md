# Transactions

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#transactions](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#transactions).

A **transaction** is the fundamental unit of ledger change (record update, contract deploy, governance vote, etc.).

Each transaction includes: **Sender**, **Payload**, **Nonce**, **Signature**, **Timestamp**. All mutations are **atomic** — full success or full rollback, no partial state.

Phase 1 gretelemetry evidence reaches the ledger as `TELEMETRY_MINT` block candidates → mint queue → signed chain submission via the sovereign-ecosystem [tegalchain/submitter](https://github.com/Shootle/sovereign-ecosystem/tree/main/tegalchain/submitter). Committed **blocks** are formed by the ordering service — see [blocks.md](./blocks.md). Full **lifecycle** — see [transaction-flow.md](./transaction-flow.md).
