# What is Tegalchain?

Tegalchain is a **permissioned distributed ledger protocol** designed for high-throughput, auditable record-keeping across multi-party networks. Unlike public blockchain networks optimised for open participation, Tegalchain prioritises **deterministic finality**, **regulatory compliance**, and **fine-grained access control** — making it well-suited for institutional, governmental, and enterprise deployments.

## At its core

Tegalchain provides:

- A **shared, tamper-evident ledger** accessible to all permissioned participants
- A **smart contract runtime** for encoding business logic on-chain
- An **on-chain governance** system for protocol upgrades and network-wide decisions
- A **pluggable consensus layer** supporting multiple Byzantine Fault Tolerant (BFT) algorithms

| Core capability | In this repo |
|-----------------|--------------|
| Tamper-evident permissioned ledger | **Phase 1** — mint queue, evidence hashes, Qortal submitter; tegalid + registry gate access |
| Smart contract runtime | **Target** — CosmWasm workspace (`tegalchain-core/contracts/`); Transynths, Voixcoin vault, PoREX |
| On-chain governance | **Specified** — TEGAL/uteg, DAO policy ([TEGAL-TOKENS.md](./contracts/TEGAL-TOKENS.md)); chain modules pending |
| Pluggable BFT consensus | **Target** — Cosmos SDK / Tendermint-class BFT on Replit build; PoREF is evidence-layer consensus, not base BFT |
| Gossip data plane | **Target** — restricted P2P gossip after ordering; CometBFT block sync among validators; channel peers on Cosmos build |
| Endorsement policies | **Specified** — per-contract logical org expressions; **Phase 1** gretelemetry uses simplified single-oracle gate |
| Contract lifecycle | **Target** — governed Package → Install → Approve → Commit on CosmWasm channel |
| Contract interface | **Target** — named invoke/query functions with transaction context on CosmWasm runtime |
| Contract best practices | **Specified** — domain-scoped, validated, deterministic, idempotent contract design |
| Client applications | **Phase 1 partial** — producer + submitter clients; full **Tegalchain SDK** on Cosmos target |
| State database | **Target** — LevelDB or CouchDB per peer; deployment-time choice; does not affect consensus |
| Deterministic finality | **Specified** — irreversible at commit; Phase 1 `submitted` + `submit_ref` in mint queue |
| State access patterns | **Specified** — `get` / `put` / `delete` / `get_range` / `get_query` / `get_history` on `ctx.state` |
| Network configuration | **Specified** — genesis config block + update history; Phase 1 `greenledger_genesis_config()` |
| Protocol upgrades | **Specified** — capability flags + node verify + `ENABLE_CAPABILITY` config tx |
| Access control lists | **Specified** — system function ACLs on channel config |

Greenledger (gretelemetry, Auditrail, PoR) runs **on** this core — see below. Full stack index: [PROTOCOL-STACK.md](./PROTOCOL-STACK.md) (**TP-103** GreenLedger).

## Transactions

A **transaction** is the fundamental unit of change on the Tegalchain ledger. Every mutation to ledger state — whether updating a record, deploying a contract, or casting a governance vote — is expressed as a transaction.

Each transaction contains:

| Field | Role |
|-------|------|
| **Sender** | Identity of the initiating permissioned participant |
| **Payload** | Operation to perform (contract invocation, asset transfer, evidence record, etc.) |
| **Nonce** | Sequence number preventing replay attacks |
| **Signature** | Cryptographic proof of sender authorisation |
| **Timestamp** | Wall-clock time when the transaction was created |

Transactions are **atomic**: they either succeed completely or fail completely, with no partial state changes applied.

### Greenledger / Phase 1 mapping

| Transaction field | This repo (today) |
|-------------------|-------------------|
| Sender | `tegal_address` / `tegalid_did` on `TELEMETRY_MINT` block candidates ([tegalchain/mint.py](../tegalchain/mint.py)) |
| Payload | `mint_payload`, `block_candidate` (gretelemetry evidence → Auditrail-bound state update) |
| Nonce | Chain account nonce on submit (target); **application replay guard** via `telemetry_hash` dedupe in mint queue |
| Signature | Producer HMAC on gretelemetry; submitter signs chain tx with `TEGALCHAIN_PRIVKEY` (Qortal `tx.pl`) |
| Timestamp | `timestamp` on telemetry and block candidate |
| Atomicity | Queue row → single submit or outbox write; failed submit stays pending or marks failed — no partial mint enqueue |

Gretelemetry **producer** signatures authenticate evidence at the oracle. **Ledger** transactions are signed by the permissioned submitter identity when draining the mint queue.

## Blocks

Transactions are grouped into **blocks** by the **ordering service**. A block is an ordered, tamper-evident bundle of transactions anchored to the previous block via a cryptographic hash, forming a chain.

```text
Block N-1          Block N            Block N+1
┌──────────┐       ┌──────────┐       ┌──────────┐
│ Header   │◄──────│ Header   │◄──────│ Header   │
│ Hash N-2 │       │ Hash N-1 │       │ Hash N   │
│ Txs …    │       │ Txs …    │       │ Txs …    │
└──────────┘       └──────────┘       └──────────┘
```

The block **header** contains:

| Field | Role |
|-------|------|
| **Previous block hash** | Links to parent block — tamper-evident chain |
| **Merkle root** | Commitment to all transactions in the block |
| **Block number** | Height / sequence in the ledger |
| **Proposer identity** | Permissioned participant that ordered this block |
| **Consensus metadata** | BFT round, votes, or ordering-service proof |

### Greenledger / Phase 1 mapping

| Block concept | This repo (today) |
|---------------|-------------------|
| Ordering service | **Target** — BFT block proposer on Cosmos SDK build; Qortal block minter on current lab node |
| Transactions in block | Drained mint-queue rows → individual chain txs (batch submit via [tegalchain/submitter](../tegalchain/submitter/)) |
| Tamper-evident chain | Inherited from underlying node (Qortal today); Tegalchain header model on Cosmos target |
| `block_candidate` in Python bridge | **Application artifact** — pre-chain `TELEMETRY_MINT` envelope, not a ledger block header |

Naming note: `mint_from_telemetry()` returns a **`block_candidate`** JSON object — a proposed ledger transaction bundle for the queue, not a committed Tegalchain block. Committed blocks are produced by the ordering service after consensus.

## Finality

Tegalchain provides **deterministic finality**: once a transaction is included in a **committed block**, it is **irreversible**. There is:

- **No fork risk** among permissioned channel peers after BFT commit  
- **No probabilistic finality** (unlike proof-of-work confirmation waiting)  
- **No confirmation depth** — a single commit is final  

This property is essential for use cases where reversal of a committed transaction would be legally or operationally unacceptable (regulated assets, audit trails, institutional settlement).

```text
Order → Validate → Commit → FINAL (irreversible)
                              ↑
                    no reorg / no depth counter
```

### Compared to public chains

| Property | Public PoW-style | Tegalchain (permissioned BFT) |
|----------|------------------|-------------------------------|
| Finality model | Probabilistic (deeper = safer) | Deterministic at commit |
| Fork handling | Longest-chain reorg | BFT quorum — no competing forks on channel |
| Client UX | Wait N confirmations | Commit event = final |

### Relation to transaction flow

Finality applies at phase **5 — Validation and commit**. Until then, a transaction proposal may fail endorsement, ordering, or validation. After commit, [gossip](#gossip-protocol-data-plane) propagates the **final** block to all peers and each updates its [state database](#state-database).

### Greenledger / Phase 1 mapping

| Finality concept | This repo (today) |
|------------------|-------------------|
| Committed / final | Mint queue `status=submitted` + chain `submit_ref` ([tegalchain/finality.py](../tegalchain/finality.py)) |
| Not final | `pending`, `outboxed`, `failed` — may retry or reject; not ledger-final |
| Irreversibility guard | `assert_no_reorg()` on submit reference; Auditrail binds post-commit evidence |
| BFT finality | **Target** — CometBFT instant finality on Cosmos build; Qortal lab inherits node commit semantics |

Phase 1 treats **`submitted`** queue rows (with a chain signature) as **application-observed finality** for gretelemetry mint records. Full channel BFT finality is on the Cosmos target.

## Transaction flow

The full transaction lifecycle has **five phases**:

1. **Proposal** — the client constructs a transaction proposal and sends it to the endorsing peers specified by the endorsement policy  
2. **Simulation** — each endorsing peer simulates the transaction (executes the contract against a snapshot of current state) and returns a signed read/write set  
3. **Endorsement collection** — the client collects signed endorsements from enough peers to satisfy the endorsement policy  
4. **Ordering** — the client submits the endorsed transaction to the ordering service, which assigns it a sequence position and batches it into a block  
5. **Validation and commit** — every peer on the channel validates the block (checks endorsements, detects conflicts) and commits valid transactions to the ledger  

```text
Client → Endorse → Endorse → Collect → Order → Validate → Commit
         Peer 1    Peer 2              Service   All Peers  All Peers
```

### Greenledger / Phase 1 mapping

| Phase | Tegalchain protocol | This repo (today) |
|-------|---------------------|-------------------|
| **Proposal** | Client builds signed tx proposal | Producer builds signed gretelemetry; mint worker forms `TELEMETRY_MINT` `block_candidate` |
| **Simulation** | Endorsers simulate contract vs state snapshot | Mint worker validates schema + simulates mint eligibility (tegalid, project registry, reward mapping) |
| **Endorsement collection** | Collect endorsements per policy | **Simplified** — single **gretelemetry oracle** gate + producer HMAC (+ optional ZK); multi-peer endorsement **target** on Cosmos channel |
| **Ordering** | Ordering service sequences and blocks | Mint queue → [submitter](../tegalchain/submitter/) → chain node ordering / minter |
| **Validation and commit** | Peers validate block and commit | Chain node (Qortal lab today; BFT peers on target) commits tx; Auditrail correlation post-commit |

The oracle path is the **Phase 1 endorsement edge** for gretelemetry: it replaces a full endorser mesh for evidence ingress while the permissioned chain still performs ordering, validation, and commit. Contract invocations (Transynths, Voixcoin vault, governance) follow the full five-phase flow on the **target** CosmWasm runtime.

After **ordering**, committed blocks and ledger state are disseminated via **gossip** (see below) — not by a central broadcast coordinator.

## Endorsement policies

Before a transaction can be submitted to the **ordering service**, it must satisfy an **endorsement policy** — a set of rules specifying which peers must sign the transaction's **read/write set** (the simulated state delta produced during endorsement).

Endorsement policies are expressed as **logical expressions over organisations** (channel members and their endorsing peers):

```python
AND('OrgA.peer', 'OrgB.peer')                              # Both OrgA and OrgB must endorse
OR('OrgA.peer', 'OrgB.peer')                               # Either OrgA or OrgB must endorse
OutOf(2, 'OrgA.peer', 'OrgB.peer', 'OrgC.peer')            # Any 2 of 3 must endorse
```

Each expression resolves to a set of **endorsing peers** that must simulate the transaction and return signed endorsements. The client collects enough signatures to satisfy the policy before submitting to ordering.

### Policy scope and governance

| Aspect | Rule |
|--------|------|
| **Binding** | Endorsement policies are set **per smart contract** (or chaincode / CosmWasm instance) |
| **Updates** | Policies can be changed through **on-chain governance** (TEGAL/uteg DAO on target runtime) |
| **Validation** | Commit-phase peers re-check that collected endorsements satisfy the contract's policy |
| **Organisations** | `Org*.peer` identifiers map to permissioned org membership on the channel (tegalid / MSP-class identity on target) |

Nested expressions (e.g. `AND(OR(...), ...)`) compose the same way on the target runtime; the primitives above are the building blocks.

### Relation to transaction flow

| Phase | Endorsement policy role |
|-------|-------------------------|
| **Proposal** | Client discovers which peers to contact from the contract's policy |
| **Simulation** | Each required endorser executes the tx against a state snapshot |
| **Endorsement collection** | Client gathers signed read/write sets until the policy expression is satisfied |
| **Ordering** | Submission rejected if endorsements do not meet policy |
| **Validation and commit** | All channel peers verify endorsements against policy before commit |

```text
Contract policy → Proposal → Simulate (required peers) → Collect signatures → Order
```

### Greenledger / Phase 1 mapping

| Endorsement concept | This repo (today) |
|---------------------|-------------------|
| Per-contract policy | **Target** — CosmWasm contracts (Transynths, Voixcoin vault, governance) carry org expressions on Cosmos build |
| Gretelemetry ingress | **Simplified** — implicit `AND('GreTelemetryOracle')` via [mint worker](../integrations/mint_worker/server.py): schema + tegalid + registry + optional ZK |
| Multi-org evidence | **Target** — e.g. `OutOf(2, 'ZeegateOrg', 'BytenergyOrg', 'OracleOrg')` for cross-subsystem attestation |
| Policy updates | **Specified** — [TEGAL-TOKENS.md](./contracts/TEGAL-TOKENS.md) governance; not yet on-chain in Phase 1 bridge |

Phase 1 does **not** implement a general policy evaluator in Python — the mint worker is a **fixed single-endorser gate** for gretelemetry. Full `AND` / `OR` / `OutOf` evaluation is a **target** capability on the CosmWasm channel runtime.

## Contract lifecycle

Smart contract **deployment and upgrade** follow a **governed lifecycle** so that no single organisation can unilaterally deploy or update a contract that affects shared channel state.

```text
Package → Install → Approve → Commit → Active on channel
```

| Phase | Description |
|-------|-------------|
| **Package** | The contract is compiled and packaged into a deployment archive (CosmWasm `.wasm` artifact on target) |
| **Install** | The package is installed on the peers of each organisation that will run it |
| **Approve** | Each organisation's admin approves the contract definition — including its **endorsement policy** and instantiation parameters |
| **Commit** | Once enough organisations have approved, the contract definition is committed to the channel and becomes **active** |

This lifecycle applies to **new deployments** and **definition updates** (policy changes, version upgrades) that affect shared ledger state.

### Why multi-org approval matters

| Risk without lifecycle | Lifecycle control |
|------------------------|-------------------|
| One org deploys malicious or buggy contract code | All participating orgs must install and approve |
| Endorsement policy changed without consent | Policy is part of the approved definition at **Approve** |
| Shared state corrupted by unilateral upgrade | **Commit** requires a channel threshold before activation |

Contract lifecycle is separate from the **transaction flow** (proposal → endorse → order → commit): lifecycle governs **what code and policies exist** on the channel; transaction flow governs **individual invocations** of an already-active contract.

### Relation to endorsement policies and governance

- The **Approve** step binds the contract's [endorsement policy](#endorsement-policies) into the channel definition  
- **Policy updates** after commit follow the same lifecycle (or an on-chain governance path defined in [TEGAL-TOKENS.md](./contracts/TEGAL-TOKENS.md))  
- **Instantiate** transactions against an active contract still require endorsements per that policy  

```text
Lifecycle:  Package → Install → Approve (policy + code) → Commit → active contract
Invocation: Proposal → Simulate → Endorse → Order → Validate → Commit
```

### Greenledger / Phase 1 mapping

| Lifecycle phase | This repo (today) |
|-----------------|-------------------|
| **Package** | **Target** — `make -C tegalchain-core/contracts build` produces CosmWasm wasm (Transynths, Voixcoin vault, PoREX) |
| **Install** | **Target** — store wasm on org endorsing peers on Cosmos channel |
| **Approve** | **Target** — multi-org admin approval (Zeegate org, utility orgs, foundation validators) |
| **Commit** | **Target** — channel commit via BFT ordering service |
| Phase 1 bridge | **No contract deploy** — Python mint worker + Qortal submitter; gretelemetry `TELEMETRY_MINT` is application evidence, not CosmWasm lifecycle |

Greenledger contracts (Transynths, Voixcoin, governance modules) are **specified** in docs and `tegalchain-core/contracts/` but follow full lifecycle only on the **Cosmos SDK target** — not on the Phase 1 Qortal lab bridge.

## Contract interface

A Tegalchain smart contract exposes **named functions** that clients can **invoke** (state-changing) or **query** (read-only). Each function receives:

| Input | Role |
|-------|------|
| **Transaction context** (`ctx`) | Access to ledger state, transaction metadata, and caller identity |
| **Arguments** | Parameters passed by the client |

### Transaction context

The context object is provided by the runtime during simulation and execution:

| Context member | Role |
|----------------|------|
| `ctx.state` | Key-value ledger state scoped to the contract (get, put, exists) |
| `ctx.identity` | Permissioned caller identity (org, tegalid / MSP-class ID on target) |
| Transaction metadata | Nonce, timestamp, channel ID, endorsing peer info (runtime-supplied) |

**Invoke** functions mutate state through `ctx.state` and flow through the full [transaction lifecycle](#transaction-flow) (endorsement → ordering → commit). **Query** functions read state only and do not produce ledger writes.

### Example (pseudocode)

```python
class AssetContract:

    def create_asset(self, ctx, asset_id: str, owner: str, value: int):
        """Create a new asset on the ledger (invoke)."""
        if ctx.state.exists(asset_id):
            raise Error(f"Asset {asset_id} already exists")
        asset = {"id": asset_id, "owner": owner, "value": value}
        ctx.state.put(asset_id, asset)

    def transfer_asset(self, ctx, asset_id: str, new_owner: str):
        """Transfer ownership of an asset (invoke)."""
        asset = ctx.state.get(asset_id)
        if not asset:
            raise Error(f"Asset {asset_id} not found")
        caller = ctx.identity.get_id()
        if asset["owner"] != caller:
            raise Error("Only the current owner can transfer this asset")
        asset["owner"] = new_owner
        ctx.state.put(asset_id, asset)

    def get_asset(self, ctx, asset_id: str):
        """Query an asset (read-only)."""
        return ctx.state.get(asset_id)
```

Invoke paths (`create_asset`, `transfer_asset`) require [endorsement](#endorsement-policies) per the contract policy before ordering. `get_asset` is a query — no endorsement collection or commit.

### Relation to transaction flow and lifecycle

| Concern | Governs |
|---------|---------|
| [Contract lifecycle](#contract-lifecycle) | Deploying the contract code that defines these functions |
| [Endorsement policies](#endorsement-policies) | Which org peers must simulate each **invoke** |
| [Transaction flow](#transaction-flow) | Proposal → simulate → endorse → order → commit for invokes |
| Contract interface | Function names, arguments, and `ctx` usage inside the wasm module |

On the **CosmWasm target**, invokes map to `execute` messages and queries map to `query` messages; the pseudocode above illustrates the same semantics.

### Greenledger / Phase 1 mapping

| Interface concept | This repo (today) |
|-------------------|-------------------|
| Named invoke/query API | **Target** — Rust CosmWasm contracts under [tegalchain-core/contracts/](../tegalchain-core/contracts/) (Transynths, Voixcoin vault, PoREX) |
| `ctx.state` | CosmWasm `deps.storage` / contract-local KV |
| `ctx.identity` | `info.sender` + tegalid-bound addresses on channel |
| Gretelemetry bridge | **Not a smart contract invoke** — Phase 1 uses Python `TELEMETRY_MINT` block candidates via oracle + mint queue; equivalent ledger writes land on target via PoRE / evidence contracts |

## Contract best practices

Tegalchain contracts run on **multiple endorsing peers** that must produce **identical simulation results** before ordering. Follow these rules when authoring CosmWasm modules (or equivalent chaincode):

| Practice | Rationale |
|----------|-----------|
| **Keep contracts small and focused** | One contract per business domain — easier audit, lifecycle approval, and endorsement policy tuning |
| **Validate all inputs** | Never trust client-supplied data; reject malformed IDs, negative amounts, and unauthorized callers at the contract boundary |
| **Use deterministic operations only** | Endorsers simulate independently — avoid RNG, external API calls, or wall-clock logic that can diverge across peers |
| **Write idempotently where possible** | Operations safe to retry simplify client error handling and outbox-style resubmission |

### Determinism and endorsement

Non-deterministic code breaks the [transaction flow](#transaction-flow): if two endorsers simulate the same invoke and produce different read/write sets, the transaction cannot be ordered consistently.

| Avoid | Prefer |
|-------|--------|
| `rand()`, oracle HTTP calls, chain-external price feeds inside invoke | Values passed as **arguments** from an endorsed upstream tx, or read from **committed ledger state** |
| `now()` / system time for business logic | Block height or transaction timestamp from **ctx** metadata (same on all peers for a given simulation) |
| Hidden side effects | Pure state transitions keyed by explicit arguments |

### Idempotency patterns

Design invokes so duplicate submission with the same logical key does not corrupt state:

```text
create_if_absent(id)   — second call with same id fails cleanly (see AssetContract example)
set_status(id, DONE)   — transition only from expected prior state
dedupe_key in payload  — reject if evidence hash / nonce already recorded
```

Gretelemetry **telemetry_hash** dedupe in the Phase 1 mint queue follows the same idempotency principle at the application layer.

### Greenledger / Phase 1 mapping

| Practice | Greenledger application |
|----------|-------------------------|
| Small, focused contracts | Separate wasm modules per Transynth (`tXcarbon`, `tXbiodiversity`, `tXwater`, `tXsoil`, `tXIREC`, `tXenergy`, `tXtel`), Voixcoin vault, PoREX exchange, governance |
| Input validation | CosmWasm `ExecuteMsg` enums + explicit bounds; oracle validates gretelemetry schema before chain ingress |
| Determinism | Evidence amounts and PA metadata committed as **arguments** — not fetched live from DePIN nodes inside wasm |
| Idempotency | Mint queue + `telemetry_hash`; on-chain evidence records keyed by hash on target |

## Client applications

**Client applications** are off-chain software that interacts with the permissioned network through the **Tegalchain SDK**. Clients orchestrate the [transaction flow](#transaction-flow) from the participant side — they do not hold ledger state themselves.

Clients:

1. **Construct and sign transaction proposals**  
2. **Submit proposals to peers for endorsement** (simulation + signed read/write sets)  
3. **Submit endorsed transactions to the ordering service**  
4. **Query ledger state** via peer read operations  

```text
Client SDK
  ├─ sign proposal ──────────► endorsing peers
  ├─ collect endorsements ◄──── endorsing peers
  ├─ submit endorsed tx ───────► ordering service
  └─ query (read-only) ────────► peer ledger API
```

### Client responsibilities by phase

| Phase | Client action |
|-------|---------------|
| **Proposal** | Build tx payload, set nonce/timestamp, sign with permissioned identity |
| **Simulation / endorsement** | Send proposal to required org peers; gather signatures until [endorsement policy](#endorsement-policies) is satisfied |
| **Ordering** | Submit endorsed bundle to ordering service (or gateway) |
| **Query** | Call contract query endpoints on any channel peer — no endorsement or commit |

Invoke paths use the full client flow above. **Query** paths skip endorsement and ordering.

### SDK surface (target)

The Tegalchain SDK wraps channel discovery, tegalid-backed signing, endorsement collection, ordering submission, and query helpers so application code does not reimplement protocol wiring.

| SDK concern | Role |
|-------------|------|
| Identity / signing | tegalid keys, org MSP-class certs on target |
| Contract calls | Serialize [invoke/query](#contract-interface) messages |
| Endorsement | Policy evaluation, peer routing, signature aggregation |
| Ordering | Gateway or BFT client submission |
| Events | Listen for commit notifications (post-[gossip](#gossip-protocol-data-plane)) |

### Greenledger / Phase 1 mapping

Phase 1 splits client responsibilities across **specialised components** rather than a single SDK binary:

| Client role | This repo (today) |
|-------------|-------------------|
| Construct + sign proposal | **Producers** — [zeegate_telemetry/client.py](../integrations/zeegate_telemetry/client.py), [bytenergy-utility/client.py](../bytenergy-utility/client.py), Android **GreTelemetry** (signed gretelemetry, not full tx proposal) |
| Submit for endorsement | Producers `POST` to [mint worker](../integrations/mint_worker/) (oracle endorsement edge) |
| Endorsement collection | **Simplified** — single oracle response; multi-peer collection **target** via SDK |
| Submit to ordering | [tegalchain/submitter](../tegalchain/submitter/) drains mint queue → chain node |
| Query ledger state | **Target** — peer query API / CosmWasm `query`; Qortal lab reads ad hoc today |

```text
Zeegate / Bytenergy / Android  →  mint worker (endorse)  →  mint queue  →  submitter (order)  →  chain
         producer client              oracle edge              bridge           ordering client
```

Edge producers are **ingress clients** — they sign gretelemetry and never talk to endorsers or ordering directly. The submitter is the **permissioned ordering client** for Phase 1 chain writes. A unified Tegalchain SDK consolidates these paths on the **Cosmos target**.

## Gossip protocol (data plane)

Tegalchain uses a **restricted gossip protocol** to complement the **ordering service**. Gossip disseminates **already-ordered** ledger data and peer state across permissioned peers without relying on a central coordinator for the data plane.

Gossip does **not** replace ordering, BFT finality, or endorsement policy — it propagates what consensus has already committed.

```text
Ordering service  →  canonical block + tx order (consensus plane)
        ↓
Gossip mesh       →  blocks, headers, state deltas, peer metadata (data plane)
        ↓
Channel peers     →  validate → commit to local ledger
```

### What gossip provides

| Capability | Role |
|------------|------|
| **Decentralized dissemination** | Committed blocks and state spread peer-to-peer |
| **Fault tolerance** | Peers catch up if one relay is unavailable |
| **Peer state sync** | Liveness, channel membership, protocol version |
| **No central data coordinator** | Every permissioned peer participates in propagation |
| **Eventual consistency** | All channel peers receive the same committed history |

### Restricted (permissioned) gossip

Tegalchain gossip is **allowlisted**, not public open mesh:

- Only **channel members** with valid org / tegalid identity may join the gossip mesh  
- Messages are **authenticated** (signed by peer identity)  
- **Raw gretelemetry** from edge producers is **not** gossiped — only oracle-approved, **committed** ledger artifacts  
- Private channel data (e.g. scoped PA metadata) may use **channel-bound** gossip collections  

### What is gossiped vs not

| Gossiped (after commit) | Not gossiped |
|-------------------------|--------------|
| Block headers and bodies | Pre-order transaction proposals at edge |
| Merkle roots / block hashes | Raw subsystem CDR, meter blobs |
| State sync snapshots / deltas | Unendorsed gretelemetry |
| Peer capability and liveness | Anonymous public peer discovery |

### Relation to ordering and transaction flow

| Plane | Component | Responsibility |
|-------|-----------|----------------|
| **Consensus** | Ordering service + BFT | Sequence, propose, finalize blocks |
| **Data** | Gossip protocol | Propagate finalized blocks and state to all peers |
| **Ingress** | Gretelemetry oracle | Evidence endorsement edge (Phase 1) |

```text
… → Order (ordering service) → Gossip → Validate → Commit
                              ↑
                    all channel peers
```

### Greenledger / Phase 1 mapping

| Gossip concept | This repo (today) |
|----------------|-------------------|
| Gossip mesh | **Target** — CometBFT P2P among validators on Cosmos build; Qortal peer sync on lab node |
| Committed block propagation | Follows chain node submitter ([tegalchain/submitter](../tegalchain/submitter/)) |
| Restricted membership | Maps to tegalid / org channel membership (**target**) |
| Edge telemetry | Stays on HTTP oracle path — **never** gossip from Zeegate/Bytenergy directly |

## State database

Each **peer** maintains a **state database** — a queryable key-value store that reflects the **current ledger state** after commit. [Client query](#client-applications) operations and contract **read** paths resolve against this store on the peer serving the request.

Tegalchain supports two state database backends:

| Backend | Description | Best for |
|---------|-------------|----------|
| **LevelDB** | Embedded key-value store | Simple key lookups, low operational overhead |
| **CouchDB** | Document-oriented database with rich query support | Complex queries, JSON-structured state |

The choice of state database is a **deployment-time decision** and does **not** affect consensus or ledger data — all peers on a channel commit the same ordered transactions; only the **local query engine** differs.

```text
Commit → peer state DB (LevelDB or CouchDB) → query / contract read
```

### Relation to contract interface and clients

| Concern | State database role |
|---------|---------------------|
| [Contract interface](#contract-interface) `ctx.state` | Invoke writes update committed KV state; persisted in the peer state DB |
| [Client applications](#client-applications) query | Off-chain clients read current state via peer query API backed by the state DB |
| [Gossip](#gossip-protocol-data-plane) | Propagates blocks; peers apply commits to rebuild/update local state DB |
| Endorsement simulation | Uses a **state snapshot** consistent with committed DB at simulation time |

Design [contract state](#contract-best-practices) for the backend you deploy: flat keys suit LevelDB; JSON documents and Mango-style selectors suit CouchDB.

### Greenledger / Phase 1 mapping

| State DB concept | This repo (today) |
|------------------|-------------------|
| Peer state database | **Target** — Cosmos SDK app DB (LevelDB/RocksDB + IAVL) on channel peers; Qortal node local store on lab |
| CouchDB rich queries | **Target** — JSON evidence / Transynth metadata queries; optional CouchDB sidecar or indexer on enterprise deployments |
| Application queue | Phase 1 [mint queue](../tegalchain/) (SQLite) — **outbox**, not peer ledger state |
| Auditrail | Verified record correlation post-commit — complementary audit layer, not a substitute for peer state DB |

Phase 1 bridge components do not configure peer state DB backends; that is a **chain node deployment** concern on the Cosmos target.

## State access patterns

Smart contracts interact with ledger state through the **state API** exposed on `ctx.state` during invoke and query simulation:

| Operation | Description |
|-----------|-------------|
| `state.get(key)` | Read a single key |
| `state.put(key, value)` | Write a single key |
| `state.delete(key)` | Delete a key |
| `state.get_range(start, end)` | Range query over keys `[start, end)` |
| `state.get_query(expression)` | Rich query (**CouchDB only**) |
| `state.get_history(key)` | Full history of a key's values |

```text
Invoke → ctx.state.put / delete → committed peer state DB
Query  → ctx.state.get / get_range / get_query / get_history → read-only
```

### Backend constraints

| Operation | LevelDB | CouchDB |
|-----------|---------|---------|
| `get`, `put`, `delete` | Yes | Yes |
| `get_range` | Yes | Yes |
| `get_history` | Yes | Yes |
| `get_query` | **No** | Yes (Mango-style selector) |

Rich queries require the CouchDB [state database](#state-database) backend. LevelDB deployments should use explicit keys or `get_range`.

### Relation to contract interface and best practices

- [Contract interface](#contract-interface) — handlers receive `ctx.state` implementing this API  
- [Contract best practices](#contract-best-practices) — validate inputs before `put`; use deterministic keys for idempotency  
- Endorsement simulation — all endorsers execute the same state transitions against a snapshot  

### Greenledger / Phase 1 mapping

| State API | This repo (today) |
|-----------|-------------------|
| Full API surface | [tegalchain/state_access.py](../tegalchain/state_access.py) (`ContractState`) for simulation/tests |
| CosmWasm target | Maps to `deps.storage` + optional CouchDB indexer sidecar |
| Gretelemetry evidence | Keys like `state_key` on `TELEMETRY_MINT`; history via Auditrail on target |

## Network configuration

The **network configuration** (config block) is a special block that captures the **current operational parameters** of a channel:

| Section | Contents |
|---------|----------|
| **Membership** | Which organisations belong to the channel |
| **Ordering service parameters** | Number of orderers, block size limits, batch timeouts |
| **Application parameters** | Endorsement policy defaults, access control lists |
| **Capabilities** | Which protocol version features are enabled |

Every channel has:

1. A **genesis config block** (block 0) — initial channel creation  
2. A **history of configuration updates** — each incrementing the config sequence  

```text
Block 0 (genesis config) → config update 1 → config update 2 → … → current config
```

Configuration updates are committed like other channel transactions and require appropriate **governance / admin policy** (multi-org approval on target).

### Configuration update process

Updating channel configuration follows a **policy-gated proposal workflow**:

1. **Proposal** — an administrator generates a config update proposal describing the desired change  
2. **Signature collection** — the proposal is distributed to relevant administrators for signatures  
3. **Ordering submission** — once enough signatures satisfy the **modification policy**, the update is submitted to the ordering service  
4. **Commit** — the ordering service validates and commits the config update as a **special transaction**  
5. **Peer sync** — all peers update their local channel configuration  

```text
Admin proposal → collect admin signatures → order → commit config tx → peers reload config
```

Implementation: [tegalchain/network_config.py](../tegalchain/network_config.py) — `ConfigUpdateWorkflow`, `ModificationPolicy`, `commit_proposal()`.

### Membership management

#### Adding a new organisation

Adding a new organisation to a channel requires:

1. The new organisation provides its **CA root certificate** and **MSP definition**  
2. An existing admin submits a config update proposal adding the new org's MSP  
3. Sufficient existing channel members approve the proposal (modification policy)  
4. The new organisation's peers can join the channel once the update commits  

#### Removing an organisation

Organisation removal follows the same config update process but **removes the org's MSP** from membership. After removal:

- The organisation's certificates are **no longer valid for new transactions**  
- **Historical records** on the ledger remain intact  

Phase 1 bridge tracks removed orgs in `ChannelConfigHistory.removed_orgs` and exposes `is_org_active()`.

### Relation to other protocol layers

| Layer | Config role |
|-------|---------------|
| [Endorsement policies](#endorsement-policies) | Application defaults; per-contract overrides |
| [Contract lifecycle](#contract-lifecycle) | Org membership gates Install / Approve |
| [Gossip](#gossip-protocol-data-plane) | Membership defines allowlisted peers |
| [Client applications](#client-applications) | Clients discover channel endpoints from config |
| [Finality](#finality) | Ordering parameters affect batching, not finality model |

### Greenledger / Phase 1 mapping

| Config concept | This repo (today) |
|----------------|-------------------|
| Genesis config | [tegalchain/network_config.py](../tegalchain/network_config.py) — `greenledger_genesis_config()` |
| Membership | GreTelemetryOracle, ZeegateOrg, BytenergyOrg (**target** FoundationOrg on Cosmos) |
| Application ACL | tegalid gate + [project registry](../tegalchain/project_registry.py) enforce ingress |
| Ordering params | Submitter batch `limit`; **target** BFT orderer set on Cosmos build |
| Capabilities | gretelemetry protocol version from [VERSION](../greentelemetry-protocol-spec/VERSION) |
| Config updates | `ConfigUpdateWorkflow` — propose, sign, commit; add/remove org MSP |
| Modification policy | `ModificationPolicy` — OutOf-style admin threshold (default: channel majority) |
| Org join material | `OrgMSPDefinition` — CA root cert + MSP id |
| Removed org certs | `removed_orgs` set — invalid for new txs; history preserved on ledger |

Phase 1 uses an in-code **genesis stub** — not yet persisted as block 0 on the Qortal lab node. Full config-block chain is on the Cosmos target.

## Protocol upgrades

Tegalchain uses a **capabilities system** to manage protocol upgrades safely on running networks. A **capability** is a named flag that enables a new protocol feature. Before enabling a capability, **all nodes** must run software that supports it.

Upgrade sequence:

1. **All nodes upgrade** their software  
2. **Administrators verify** all nodes report the new version  
3. A **capabilities update** is proposed and approved via the [config update process](#configuration-update-process)  
4. The capability **activates**, enabling the new protocol feature  

```text
Node software upgrade → verify version reports → config ENABLE_CAPABILITY → feature active
```

This sequencing ensures no node processes a transaction using a feature it does not understand.

### Greenledger / Phase 1 mapping

| Capability concept | This repo (today) |
|--------------------|-------------------|
| Capability flags | `ChannelCapabilities.features` in [network_config.py](../tegalchain/network_config.py) |
| Node version verify | [tegalchain/capabilities.py](../tegalchain/capabilities.py) — `NodeVersionReport`, `verify_all_nodes_support_capability()` |
| Enable via config | `ConfigUpdateKind.ENABLE_CAPABILITY` + `CapabilityUpgradeWorkflow` |
| Genesis enabled | `gretelemetry_oracle` — `zk_evidence_optional` enabled via upgrade workflow |

## Access control lists

**Access Control Lists (ACLs)** define which identities can invoke which **system functions**. ACLs control access to:

- **Peer administration APIs** — joining channels, installing contracts  
- **Event subscription APIs**  
- **Ledger query APIs**  
- **Config update proposal submission**  

ACLs are part of **channel configuration** (`ApplicationParameters.system_acl`) and can be updated through the [governance / config update process](#configuration-update-process) (`ConfigUpdateKind.UPDATE_ACL`).

| System function | Controlled access |
|-----------------|-------------------|
| `peer_admin` | Channel join, contract install |
| `event_subscribe` | Commit / block event streams |
| `ledger_query` | Read-only ledger API |
| `config_update` | Submit config update proposals |

Implementation: [tegalchain/access_control.py](../tegalchain/access_control.py) — `SystemFunction`, `assert_system_acl_allowed()`.

### Greenledger / Phase 1 mapping

| ACL concept | This repo (today) |
|-------------|-------------------|
| System ACL | `greenledger_system_acl_rules()` — channel admin orgs |
| Ingress gate | `access_control_list` on application params — `tegalid_gate`, `project_registry` |
| Config update ACL | Requires `CONFIG_UPDATE` permission + modification policy signatures |
| Mint worker | Implicit oracle-only ingress — not full peer admin API yet |

## How this repo uses Tegalchain

The [sovereign-ecosystem](https://github.com/Shootle/sovereign-ecosystem) monorepo deploys a **Greenledger** application on Tegalchain: environmentally sustainable DePIN and utility nodes (Zeegate, Bytenergy, future verticals) submit **greentelemetry** evidence through a single oracle; **tegalid** enforces identity and access; **Auditrail** holds verified records.

That environmental stack is one permissioned network design — not the only possible Tegalchain deployment.

| Tegalchain capability | Greenledger use in this repo |
|----------------------|------------------------------|
| Permissioned participation | tegalid `NodeBinding`, project registry, mint gate |
| Auditable records | Auditrail, gretelemetry + optional ZK on final evidence |
| Fine-grained access | Per-project `system_type`, binding HMAC, oracle rejection |
| Multi-party networks | Independent subsystems → one schema → oracle → ledger |
| Deterministic finality | Mint queue → chain submitter; evidence hashes deduped |

## Application layers on the ledger

| Layer | Role |
|-------|------|
| **PoR stack** | PoRE (resonance evidence), PoREF (foundation validators), PoREX (exchange) — see [tegalchain-core/docs/proof-of-resonance-stack.md](../tegalchain-core/docs/proof-of-resonance-stack.md) |
| **Greenledger** | Custodianless ledger for provenance assets, TEGAL/uteg, Transynths (tX*), Voixcoin |
| **Gretelemetry oracle** | Sole ingress from external producers — [GREETELEMETRY-ORACLE-BOUNDARY.md](./contracts/GREETELEMETRY-ORACLE-BOUNDARY.md) |

## Implementation notes

- **Chain core:** [tegalchain-core/](../tegalchain-core/) submodule → [Tegalchain/Tegalchain](https://github.com/Tegalchain/Tegalchain) (Qortal lineage today; Cosmos SDK + CosmWasm target on Replit/Colab)
- **Bridge:** [tegalchain/](../tegalchain/) — validate → tegalid gate → mint queue → submitter (Phase 1)
- **Not a public open chain:** open telemetry producers still pass **permissioned** mint policy (tegalid + registry); ledger access is governed, not anonymous-by-default

## Related

- [README.md](../README.md) — monorepo layout
- [GLOSSARY.md](./GLOSSARY.md) — gretelemetry naming
- [TEGAL-TOKENS.md](./contracts/TEGAL-TOKENS.md) · [VOIXCOIN.md](./contracts/VOIXCOIN.md)
- Code: [tegalchain/mint.py](../tegalchain/mint.py) (tx proposal) · [integrations/mint_worker/server.py](../integrations/mint_worker/server.py) (endorsement edge) · [tegalchain/submitter/](../tegalchain/submitter/) (ordering)
- Network: [tegalchain-core/docs/gossip.md](../tegalchain-core/docs/gossip.md) (gossip data plane) · [tegalchain-core/docs/endorsement-policies.md](../tegalchain-core/docs/endorsement-policies.md) (endorsement policies) · [tegalchain-core/docs/contract-lifecycle.md](../tegalchain-core/docs/contract-lifecycle.md) (contract lifecycle) · [tegalchain-core/docs/contract-interface.md](../tegalchain-core/docs/contract-interface.md) (contract interface) · [tegalchain-core/docs/contract-best-practices.md](../tegalchain-core/docs/contract-best-practices.md) (contract best practices) · [tegalchain-core/docs/client-applications.md](../tegalchain-core/docs/client-applications.md) (client applications) · [tegalchain-core/docs/state-database.md](../tegalchain-core/docs/state-database.md) (state database) · [tegalchain-core/docs/state-access-patterns.md](../tegalchain-core/docs/state-access-patterns.md) (state access patterns) · [tegalchain-core/docs/finality.md](../tegalchain-core/docs/finality.md) (finality) · [tegalchain-core/docs/network-configuration.md](../tegalchain-core/docs/network-configuration.md) (network configuration) · [tegalchain-core/docs/protocol-upgrades.md](../tegalchain-core/docs/protocol-upgrades.md) (protocol upgrades) · [tegalchain-core/docs/access-control-lists.md](../tegalchain-core/docs/access-control-lists.md) (access control lists)
