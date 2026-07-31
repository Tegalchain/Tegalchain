"""Block and block-candidate models.

``block_candidate`` from mint.py is a pre-chain transaction proposal — not a committed
ledger block. See docs/TEGALCHAIN.md#blocks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class BlockHeader:
    previous_block_hash: str
    merkle_root: str
    block_number: int
    proposer_identity: str


@dataclass(frozen=True, slots=True)
class CommittedBlock:
    header: BlockHeader
    transactions: tuple[dict[str, Any], ...]


def merkle_root(transactions: Sequence[dict[str, Any]]) -> str:
    """Deterministic Merkle root over canonical transaction JSON."""
    if not transactions:
        return hashlib.sha256(b"").hexdigest()

    leaves = [
        hashlib.sha256(
            json.dumps(tx, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()
        for tx in transactions
    ]
    while len(leaves) > 1:
        next_level: list[str] = []
        for index in range(0, len(leaves), 2):
            left = leaves[index]
            right = leaves[index + 1] if index + 1 < len(leaves) else left
            combined = hashlib.sha256(f"{left}{right}".encode()).hexdigest()
            next_level.append(combined)
        leaves = next_level
    return leaves[0]


def merkle_root_from_hashes(hashes: Sequence[str]) -> str:
    """Merkle root over hex hash leaves (TP-101 GTR content_hash batching)."""
    if not hashes:
        return hashlib.sha256(b"").hexdigest()
    level = list(hashes)
    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            next_level.append(hashlib.sha256(f"{left}{right}".encode()).hexdigest())
        level = next_level
    return level[0]


def merkle_proof(leaf_index: int, leaves: Sequence[str]) -> list[str]:
    """Return sibling hashes from leaf to root for inclusion verification."""
    if not leaves:
        return []
    if leaf_index < 0 or leaf_index >= len(leaves):
        raise IndexError("leaf_index out of range")

    level = list(leaves)
    index = leaf_index
    proof: list[str] = []
    while len(level) > 1:
        sibling_index = index - 1 if index % 2 == 1 else index + 1
        if sibling_index < len(level):
            proof.append(level[sibling_index])
        else:
            proof.append(level[index])
        next_level: list[str] = []
        for pos in range(0, len(level), 2):
            left = level[pos]
            right = level[pos + 1] if pos + 1 < len(level) else left
            next_level.append(
                hashlib.sha256(f"{left}{right}".encode()).hexdigest()
            )
        index //= 2
        level = next_level
    return proof


def verify_merkle_proof(leaf_hash: str, proof: Sequence[str], root: str, leaf_index: int = 0) -> bool:
    """Verify a leaf hash is included under merkle_root using sibling proof."""
    current = leaf_hash
    index = leaf_index
    for sibling in proof:
        if index % 2 == 0:
            current = hashlib.sha256(f"{current}{sibling}".encode()).hexdigest()
        else:
            current = hashlib.sha256(f"{sibling}{current}".encode()).hexdigest()
        index //= 2
    return current == root


def is_block_candidate(artifact: dict[str, Any]) -> bool:
    return artifact.get("type") == "TELEMETRY_MINT"
