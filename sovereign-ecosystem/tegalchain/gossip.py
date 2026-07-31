"""Restricted gossip data plane (Phase 1 stub).

Propagates committed blocks and state after ordering — not raw edge telemetry.
Target: CometBFT P2P. See docs/TEGALCHAIN.md#gossip-protocol-data-plane.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .block import merkle_root


class GossipMessageType(str, Enum):
    BLOCK_ANNOUNCEMENT = "block_announcement"
    STATE_DELTA = "state_delta"
    PEER_METADATA = "peer_metadata"


@dataclass(frozen=True, slots=True)
class GossipMessage:
    message_type: GossipMessageType
    channel_id: str
    payload: dict[str, Any]
    signer_peer: str


@dataclass
class GossipFanout:
    """In-memory fanout registry for tests and Phase 1 bridge hooks."""

    received: list[GossipMessage] = field(default_factory=list)

    def publish(self, message: GossipMessage) -> None:
        if message.message_type is GossipMessageType.BLOCK_ANNOUNCEMENT:
            if message.payload.get("pre_order"):
                raise ValueError("gossip must not carry pre-order proposals")
        self.received.append(message)

    def clear(self) -> None:
        self.received.clear()


def announce_committed_block(
    fanout: GossipFanout,
    *,
    channel_id: str,
    signer_peer: str,
    block_number: int,
    block_hash: str,
    merkle_root: str,
) -> GossipMessage:
    message = GossipMessage(
        message_type=GossipMessageType.BLOCK_ANNOUNCEMENT,
        channel_id=channel_id,
        signer_peer=signer_peer,
        payload={
            "block_number": block_number,
            "block_hash": block_hash,
            "merkle_root": merkle_root,
            "pre_order": False,
        },
    )
    fanout.publish(message)
    return message


def publish_submitted_transaction(
    fanout: GossipFanout,
    *,
    channel_id: str,
    signer_peer: str,
    block_number: int,
    block_candidate: dict[str, Any],
    submit_ref: str,
) -> GossipMessage:
    """Announce a committed transaction bundle on the gossip data plane."""
    root = merkle_root([block_candidate])
    block_hash = hashlib.sha256(submit_ref.encode()).hexdigest()
    return announce_committed_block(
        fanout,
        channel_id=channel_id,
        signer_peer=signer_peer,
        block_number=block_number,
        block_hash=block_hash,
        merkle_root=root,
    )
