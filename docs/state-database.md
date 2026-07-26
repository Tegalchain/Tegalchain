# State database

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#state-database](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#state-database).

Each peer maintains a **state database** — a queryable key-value store reflecting **current ledger state** after commit.

## Backends

| Backend | Description | Best for |
|---------|-------------|----------|
| **LevelDB** | Embedded key-value store | Simple key lookups, low operational overhead |
| **CouchDB** | Document-oriented database with rich query support | Complex queries, JSON-structured state |

Backend choice is **deployment-time only** — it does not affect consensus or committed ledger data.

## Usage

- **Contract invoke** — writes update committed KV state in the peer DB  
- **Client query** — read operations resolve against the peer state DB  
- **Gossip + commit** — peers apply ordered blocks to keep the DB current  

See also [client-applications.md](./client-applications.md) · [contract-interface.md](./contract-interface.md) · [gossip.md](./gossip.md).

## Phase 1 (Greenledger)

The Python mint queue (SQLite) is an application **outbox**, not peer ledger state. Peer state DB configuration applies to Cosmos SDK / Qortal chain node deployments on the target build.
