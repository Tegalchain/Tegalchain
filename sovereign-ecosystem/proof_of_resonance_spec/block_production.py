"""TP-102 block production — validator set selection and BFT parameters."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

EPOCH_BLOCK_COUNT = 1_000
MAX_ACTIVE_VALIDATORS = 100
FINALITY_SUPERMAJORITY_NUMERATOR = 2
FINALITY_SUPERMAJORITY_DENOMINATOR = 3


@dataclass(frozen=True, slots=True)
class ValidatorSetMember:
    validator_id: str
    resonance_score: float


@dataclass(frozen=True, slots=True)
class ActiveValidatorSet:
    epoch_index: int
    members: tuple[ValidatorSetMember, ...]
    max_byzantine: int
    finality_threshold: int

    def to_dict(self) -> dict[str, object]:
        return {
            "epoch_index": self.epoch_index,
            "validator_count": len(self.members),
            "max_byzantine": self.max_byzantine,
            "finality_threshold": self.finality_threshold,
            "members": [
                {
                    "validator_id": m.validator_id,
                    "resonance_score": m.resonance_score,
                }
                for m in self.members
            ],
        }


def byzantine_fault_tolerance(n: int) -> int:
    """Maximum Byzantine validators tolerated: floor((N − 1) / 3)."""
    if n <= 0:
        return 0
    return (n - 1) // 3


def finality_threshold(n: int) -> int:
    """Block finality requires 2/3 + 1 supermajority signatures."""
    if n <= 0:
        return 0
    return (FINALITY_SUPERMAJORITY_NUMERATOR * n) // FINALITY_SUPERMAJORITY_DENOMINATOR + 1


def select_active_validator_set(
    eligible: list[ValidatorSetMember],
    *,
    epoch_index: int,
    max_validators: int = MAX_ACTIVE_VALIDATORS,
) -> ActiveValidatorSet:
    """Rank eligible validators by R descending; take top N = min(100, eligible_count)."""
    ranked = sorted(eligible, key=lambda m: m.resonance_score, reverse=True)
    n = min(max_validators, len(ranked))
    members = tuple(ranked[:n])
    count = len(members)
    return ActiveValidatorSet(
        epoch_index=epoch_index,
        members=members,
        max_byzantine=byzantine_fault_tolerance(count),
        finality_threshold=finality_threshold(count),
    )


def vrf_slot_seed(previous_epoch_final_block_hash: str, slot_index: int) -> int:
    """Deterministic VRF seed from previous epoch final block hash (reference stub)."""
    digest = hashlib.sha256(
        f"{previous_epoch_final_block_hash}:{slot_index}".encode()
    ).hexdigest()
    return int(digest[:16], 16)


def assign_slot_leader(
    active_set: ActiveValidatorSet,
    *,
    previous_epoch_final_block_hash: str,
    slot_index: int,
) -> str | None:
    """VRF-weighted leader rotation — higher R validators receive more slots."""
    if not active_set.members:
        return None
    seed = vrf_slot_seed(previous_epoch_final_block_hash, slot_index)
    total_weight = sum(max(m.resonance_score, 0.0) for m in active_set.members)
    if total_weight <= 0:
        return active_set.members[seed % len(active_set.members)].validator_id
    pick = (seed % 10_000) / 10_000.0 * total_weight
    cumulative = 0.0
    for member in active_set.members:
        cumulative += max(member.resonance_score, 0.0)
        if pick <= cumulative:
            return member.validator_id
    return active_set.members[-1].validator_id


def proportional_block_assignments(
    active_set: ActiveValidatorSet,
    *,
    epoch_blocks: int = EPOCH_BLOCK_COUNT,
) -> dict[str, int]:
    """Distribute epoch block assignments proportional to Resonance Score."""
    if not active_set.members:
        return {}
    total_r = sum(max(m.resonance_score, 0.0) for m in active_set.members)
    if total_r <= 0:
        base = epoch_blocks // len(active_set.members)
        return {m.validator_id: base for m in active_set.members}
    assignments: dict[str, int] = {}
    allocated = 0
    for i, member in enumerate(active_set.members):
        if i == len(active_set.members) - 1:
            assignments[member.validator_id] = epoch_blocks - allocated
        else:
            share = int(round(epoch_blocks * max(member.resonance_score, 0.0) / total_r))
            assignments[member.validator_id] = share
            allocated += share
    return assignments
