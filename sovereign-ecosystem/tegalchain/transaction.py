"""Ledger transaction model — atomic unit of ledger change.

See docs/TEGALCHAIN.md#transactions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LedgerTransaction:
    sender: str
    payload: dict[str, Any]
    nonce: int | None
    signature: str
    timestamp: int

    @classmethod
    def from_block_candidate(cls, block_candidate: dict[str, Any]) -> LedgerTransaction:
        """Build a transaction view from a ``TELEMETRY_MINT`` block candidate."""
        tx_type = block_candidate.get("type")
        if tx_type != "TELEMETRY_MINT":
            raise ValueError(f"unsupported block_candidate type: {tx_type!r}")

        return cls(
            sender=str(block_candidate["signer"]),
            payload={
                "type": tx_type,
                "namespace": block_candidate.get("namespace"),
                "mint_payload": block_candidate.get("mint_payload"),
                "state_key": block_candidate.get("state_key"),
                "telemetry_hash": block_candidate.get("telemetry_hash"),
            },
            nonce=None,
            signature=str(block_candidate.get("signature", "")),
            timestamp=int(block_candidate["timestamp"]),
        )
