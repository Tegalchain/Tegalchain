"""TP-102 validator lifecycle — registration, eligibility, suspension."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import (
    DEFAULT_MIN_R_ENV_BLOCK_PRODUCTION,
    DEFAULT_MIN_RESONANCE_BLOCK_PRODUCTION,
    DEFAULT_MIN_RESONANCE_GOVERNANCE,
    MIN_IDENTITY_TIER,
    MIN_STAKE_TEGAL,
    ValidatorResonanceDimensions,
    ValidatorResonanceProfile,
)
from .resonance import compute_resonance_score


class IdentityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class BondStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SLASHING_DISPUTE = "SLASHING_DISPUTE"
    BELOW_MINIMUM = "BELOW_MINIMUM"


@dataclass(frozen=True, slots=True)
class ValidatorRegistration:
    """On-chain registration payload (reference)."""

    validator_id: str
    identity_tier: int
    bond_tegals: int
    baseline_gtr_days: int
    jurisdiction: str
    infrastructure_provider: str
    energy_source_attestation: str
    policy_statement_uri: str


@dataclass(frozen=True, slots=True)
class ValidatorOperationalState:
    identity_status: IdentityStatus
    bond_status: BondStatus
    bond_tegals: int
    gtr_count_current_month: int
    consecutive_epochs_below_min_r: int = 0


def validate_registration(registration: ValidatorRegistration) -> list[str]:
    """Return validation errors; empty list means registration requirements met."""
    errors: list[str] = []
    if registration.identity_tier < MIN_IDENTITY_TIER:
        errors.append(
            f"identity tier {registration.identity_tier} < required Tier {MIN_IDENTITY_TIER}"
        )
    if registration.bond_tegals < MIN_STAKE_TEGAL:
        errors.append(
            f"bond {registration.bond_tegals} TEGAL < minimum {MIN_STAKE_TEGAL}"
        )
    if registration.baseline_gtr_days < 90:
        errors.append("baseline GreenTelemetry report must cover at least 90 days")
    if not registration.jurisdiction.strip():
        errors.append("operational jurisdiction is required")
    if not registration.infrastructure_provider.strip():
        errors.append("infrastructure provider is required")
    if not registration.energy_source_attestation.strip():
        errors.append("energy source attestation is required")
    if not registration.policy_statement_uri.strip():
        errors.append("Validator Policy Statement URI is required")
    return errors


def is_eligible_for_block_production(
    *,
    dimensions: ValidatorResonanceDimensions,
    state: ValidatorOperationalState,
    min_r: float = DEFAULT_MIN_RESONANCE_BLOCK_PRODUCTION,
    min_r_env: float = DEFAULT_MIN_R_ENV_BLOCK_PRODUCTION,
) -> bool:
    """Section 3.2 — epoch block production eligibility."""
    if state.identity_status != IdentityStatus.ACTIVE:
        return False
    if state.bond_status == BondStatus.SLASHING_DISPUTE:
        return False
    if state.gtr_count_current_month <= 0:
        return False
    r = compute_resonance_score(
        dimensions.r_env,
        dimensions.r_gov,
        dimensions.r_up,
        dimensions.r_cmp,
    )
    return r >= min_r and dimensions.r_env >= min_r_env


def suspension_action(
    *,
    state: ValidatorOperationalState,
    dimensions: ValidatorResonanceDimensions,
    double_signing_pending: bool = False,
    min_r: float = DEFAULT_MIN_RESONANCE_BLOCK_PRODUCTION,
    min_bond_tegals: int = 8_000,
    suspension_epochs: int = 3,
) -> str | None:
    """Return suspension/ejection action label, or None if no action."""
    if state.identity_status == IdentityStatus.REVOKED:
        return "EJECT_PERMANENT"
    if double_signing_pending:
        return "SUSPEND_PENDING_GOVERNANCE"
    if state.consecutive_epochs_below_min_r >= suspension_epochs:
        r = compute_resonance_score(
            dimensions.r_env,
            dimensions.r_gov,
            dimensions.r_up,
            dimensions.r_cmp,
        )
        if r < min_r:
            return "SUSPEND_AUTO"
    if state.bond_tegals < min_bond_tegals:
        return "SUSPEND_BOND_GRACE"
    return None


def apply_eligibility_to_profile(
    profile: ValidatorResonanceProfile,
    *,
    state: ValidatorOperationalState,
    min_r_env: float = DEFAULT_MIN_R_ENV_BLOCK_PRODUCTION,
) -> ValidatorResonanceProfile:
    """Merge operational state into a scored profile."""
    block_eligible = is_eligible_for_block_production(
        dimensions=profile.dimensions,
        state=state,
        min_r=DEFAULT_MIN_RESONANCE_BLOCK_PRODUCTION,
        min_r_env=min_r_env,
    )
    governance_eligible = (
        state.identity_status == IdentityStatus.ACTIVE
        and profile.resonance_score >= DEFAULT_MIN_RESONANCE_GOVERNANCE
    )
    return ValidatorResonanceProfile(
        validator_id=profile.validator_id,
        validator_class=profile.validator_class,
        resonance_score=profile.resonance_score,
        dimensions=profile.dimensions,
        eligible_for_block_production=block_eligible,
        eligible_for_governance=governance_eligible,
        scored_at=profile.scored_at,
        scoring_profile=profile.scoring_profile,
        gtr_count_current_month=state.gtr_count_current_month,
    )
