"""Endorsement policy expressions for pre-order transaction validation.

Phase 1 gretelemetry uses a simplified single-oracle gate; full ``AND`` / ``OR`` /
``OutOf`` evaluation is for multi-org CosmWasm channels on the target runtime.
See docs/TEGALCHAIN.md#endorsement-policies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


ORACLE_PEER_ID = "GreTelemetryOracle.peer"


class PolicyNode(Protocol):
    def satisfied_by(self, endorsed_peers: set[str]) -> bool: ...

    def required_peers(self) -> frozenset[str]: ...


@dataclass(frozen=True, slots=True)
class AndPolicy:
    peers: tuple[str, ...]

    def satisfied_by(self, endorsed_peers: set[str]) -> bool:
        return all(peer in endorsed_peers for peer in self.peers)

    def required_peers(self) -> frozenset[str]:
        return frozenset(self.peers)


@dataclass(frozen=True, slots=True)
class OrPolicy:
    peers: tuple[str, ...]

    def satisfied_by(self, endorsed_peers: set[str]) -> bool:
        return any(peer in endorsed_peers for peer in self.peers)

    def required_peers(self) -> frozenset[str]:
        return frozenset(self.peers)


@dataclass(frozen=True, slots=True)
class OutOfPolicy:
    threshold: int
    peers: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ValueError("OutOf threshold must be at least 1")
        if self.threshold > len(self.peers):
            raise ValueError("OutOf threshold cannot exceed peer count")

    def satisfied_by(self, endorsed_peers: set[str]) -> bool:
        matched = sum(1 for peer in self.peers if peer in endorsed_peers)
        return matched >= self.threshold

    def required_peers(self) -> frozenset[str]:
        return frozenset(self.peers)


def AND(*peers: str) -> AndPolicy:
    if not peers:
        raise ValueError("AND requires at least one peer")
    return AndPolicy(peers=peers)


def OR(*peers: str) -> OrPolicy:
    if not peers:
        raise ValueError("OR requires at least one peer")
    return OrPolicy(peers=peers)


def OutOf(threshold: int, *peers: str) -> OutOfPolicy:
    if not peers:
        raise ValueError("OutOf requires at least one peer")
    return OutOfPolicy(threshold=threshold, peers=peers)


DEFAULT_GREETELEMETRY_POLICY: AndPolicy = AND(ORACLE_PEER_ID)


@dataclass(frozen=True, slots=True)
class Endorsement:
    peer: str
    read_write_set_hash: str | None = None


def endorsements_satisfy_policy(
    policy: PolicyNode,
    endorsements: Sequence[Endorsement],
) -> bool:
    endorsed_peers = {item.peer for item in endorsements}
    return policy.satisfied_by(endorsed_peers)


def attach_endorsements(
    block_candidate: dict[str, object],
    endorsements: Sequence[Endorsement],
) -> dict[str, object]:
    """Return block_candidate with an ``endorsements`` list for ordering validation."""
    enriched = dict(block_candidate)
    enriched["endorsements"] = [
        {
            "peer": item.peer,
            **(
                {"read_write_set_hash": item.read_write_set_hash}
                if item.read_write_set_hash is not None
                else {}
            ),
        }
        for item in endorsements
    ]
    return enriched


def parse_endorsements_from_candidate(
    block_candidate: dict[str, object],
) -> tuple[Endorsement, ...]:
    raw = block_candidate.get("endorsements")
    if not raw:
        return ()
    if not isinstance(raw, list):
        raise ValueError("endorsements must be a list")

    parsed: list[Endorsement] = []
    for item in raw:
        if not isinstance(item, dict) or "peer" not in item:
            raise ValueError("each endorsement must include peer")
        parsed.append(
            Endorsement(
                peer=str(item["peer"]),
                read_write_set_hash=(
                    str(item["read_write_set_hash"])
                    if item.get("read_write_set_hash") is not None
                    else None
                ),
            )
        )
    return tuple(parsed)


def assert_ready_for_ordering(
    block_candidate: dict[str, object],
    policy: PolicyNode = DEFAULT_GREETELEMETRY_POLICY,
) -> None:
    """Raise ValueError if endorsements on a block candidate do not satisfy policy."""
    endorsements = parse_endorsements_from_candidate(block_candidate)
    if not endorsements_satisfy_policy(policy, endorsements):
        required = sorted(policy.required_peers())
        got = sorted({item.peer for item in endorsements})
        raise ValueError(
            f"endorsement policy not satisfied; required={required} got={got}"
        )
