"""TP-102 slashing — bond penalties and evidence payloads."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .resonance import ComplianceOffence, ComplianceInputs, compute_r_cmp


class SlashCondition(str, Enum):
    PROVABLE_DOUBLE_SIGNING = "PROVABLE_DOUBLE_SIGNING"
    EQUIVOCATION_FINALITY = "EQUIVOCATION_FINALITY"
    FABRICATED_GTR = "FABRICATED_GTR"


# Bond slash as fraction of staked bond (0.0–1.0).
BOND_SLASH_FRACTION: dict[SlashCondition, float] = {
    SlashCondition.PROVABLE_DOUBLE_SIGNING: 0.10,
    SlashCondition.EQUIVOCATION_FINALITY: 0.05,
    SlashCondition.FABRICATED_GTR: 0.20,
}

# Maps slash conditions to R_cmp compliance offences.
SLASH_TO_COMPLIANCE: dict[SlashCondition, ComplianceOffence | None] = {
    SlashCondition.PROVABLE_DOUBLE_SIGNING: ComplianceOffence.DOUBLE_SIGNING,
    SlashCondition.EQUIVOCATION_FINALITY: ComplianceOffence.EQUIVOCATION_FINALITY,
    SlashCondition.FABRICATED_GTR: None,  # permanent — handled separately
}

# Additional R_cmp penalty for equivocation (beyond base offence table if any).
EQUIVOCATION_R_CMP_PENALTY = 0.20


@dataclass(frozen=True, slots=True)
class SlashEvidence:
    """Evidence any participant MAY submit to TP-106 governance."""

    validator_id: str
    condition: SlashCondition
    proof: str
    block_heights: tuple[int, ...]
    timestamps: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "validator_id": self.validator_id,
            "condition": self.condition.value,
            "proof": self.proof,
            "block_heights": list(self.block_heights),
            "timestamps": list(self.timestamps),
        }


def compute_bond_slash_amount(
    bond_tegals: int,
    condition: SlashCondition,
) -> int:
    fraction = BOND_SLASH_FRACTION[condition]
    return int(bond_tegals * fraction)


def apply_slash_to_compliance(
    inputs: ComplianceInputs,
    condition: SlashCondition,
) -> tuple[float, bool]:
    """Return updated R_cmp and whether validator MUST be ejected."""
    if condition == SlashCondition.FABRICATED_GTR:
        return 0.0, True
    offence = SLASH_TO_COMPLIANCE[condition]
    if offence is None:
        return compute_r_cmp(inputs), False
    new_offences = inputs.offences + (offence,)
    return compute_r_cmp(
        ComplianceInputs(
            offences=new_offences,
            epochs_since_last_offence=0,
        )
    ), False


def preliminary_slash_applies(evidence: SlashEvidence) -> bool:
    """Valid evidence triggers automatic preliminary slash pending governance vote."""
    return bool(evidence.proof.strip()) and bool(evidence.validator_id.strip())
