"""Tegalchain client applications — off-chain propose, endorse, order, query.

Phase 1 splits responsibilities across producer scripts, the mint worker oracle,
and the submitter. A unified SDK consolidates these on the Cosmos target.
See docs/TEGALCHAIN.md#client-applications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from integrations.mint_worker.submit import submit_telemetry

from .endorsement import Endorsement
from .queue.store import MintQueueStore
from .submitter.drain import DrainResult, SubmitterConfig, drain_queue


@dataclass(frozen=True, slots=True)
class TransactionProposal:
    """Signed transaction proposal plus collected endorsements."""

    block_candidate: dict[str, Any]
    endorsements: tuple[Endorsement, ...]


class GreTelemetryProducerClient:
    """Ingress client: construct signed gretelemetry and submit to the oracle."""

    def __init__(self, mint_worker_url: str) -> None:
        self.mint_worker_url = mint_worker_url.rstrip("/")

    def propose_and_endorse(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST telemetry to mint worker (proposal + oracle endorsement edge)."""
        return submit_telemetry(self.mint_worker_url, payload)


class OrderingClient:
    """Ordering client: drain mint queue to the chain node ordering service."""

    def __init__(self, config: SubmitterConfig | None = None) -> None:
        self.config = config or SubmitterConfig.from_env()

    def submit_to_ordering(self, *, limit: int = 20) -> DrainResult:
        store = MintQueueStore(self.config.db_path)
        return drain_queue(store, self.config, limit=limit)


class QueryClient:
    """Read-only client — peer state DB on target; outbox helper for Phase 1 dev."""

    def query_peer_state(self, state_key: str) -> dict[str, Any]:
        raise NotImplementedError(
            "Peer state DB query is not implemented in Phase 1 bridge "
            f"(key={state_key!r}). Use CosmWasm query or Qortal RPC on target."
        )
