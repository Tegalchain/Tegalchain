# Blocks

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#blocks](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#blocks).

Transactions are ordered into **blocks** by the **ordering service**. Each block header carries: previous block hash, Merkle root of transactions, block number, proposer identity, and consensus metadata.

See also [transactions.md](./transactions.md).

Phase 1: the Python bridge enqueues **transaction** candidates (`TELEMETRY_MINT`); the chain node's ordering service commits them into blocks.
