"""State layer distinctions for the Phase 1 bridge vs peer ledger nodes.

The mint queue (SQLite) is an **application outbox** for transaction proposals.
Peer **state databases** (LevelDB / CouchDB) hold committed ledger KV state on
chain nodes. See docs/TEGALCHAIN.md#state-database.
"""

from __future__ import annotations

from enum import Enum


class StateLayer(str, Enum):
    """Where ledger-related data lives in the ecosystem."""

    APPLICATION_OUTBOX = "application_outbox"
    PEER_LEDGER = "peer_ledger"


class StateDatabaseBackend(str, Enum):
    """Peer state DB backend — deployment-time choice only."""

    LEVELDB = "leveldb"
    COUCHDB = "couchdb"


def describe_mint_queue_layer() -> str:
    return (
        "Mint queue SQLite stores pending TELEMETRY_MINT proposals (application "
        "outbox). It is not the peer state database."
    )
