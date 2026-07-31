"""TP-102 validator Resonance eligibility."""

from __future__ import annotations

from datetime import UTC, datetime

from .models import (
    DEFAULT_MIN_R_ENV_BLOCK_PRODUCTION,
    DEFAULT_MIN_RESONANCE_BLOCK_PRODUCTION,
    DEFAULT_MIN_RESONANCE_GOVERNANCE,
    ScoringProfile,
    ValidatorClass,
    ValidatorResonanceDimensions,
    ValidatorResonanceProfile,
)
from .resonance import (
    ComplianceInputs,
    EnvironmentalInputs,
    GovernanceInputs,
    UptimeInputs,
    compute_r_cmp,
    compute_r_env,
    compute_r_gov,
    compute_r_up,
    compute_resonance_score,
)


def compute_validator_resonance(dimensions: ValidatorResonanceDimensions) -> float:
    """Weighted composite Resonance score R in [0.0, 1.0]."""
    return compute_resonance_score(
        dimensions.r_env,
        dimensions.r_gov,
        dimensions.r_up,
        dimensions.r_cmp,
    )


def score_validator_dimensions(
    *,
    environmental: EnvironmentalInputs,
    governance: GovernanceInputs,
    uptime: UptimeInputs,
    compliance: ComplianceInputs,
) -> ValidatorResonanceDimensions:
    """Compute all four Resonance dimensions from observable inputs."""
    return ValidatorResonanceDimensions(
        r_env=compute_r_env(environmental),
        r_gov=compute_r_gov(governance),
        r_up=compute_r_up(uptime),
        r_cmp=compute_r_cmp(compliance),
    )


def score_validator(
    *,
    validator_id: str,
    validator_class: ValidatorClass,
    dimensions: ValidatorResonanceDimensions,
    scoring_profile: ScoringProfile = ScoringProfile.PHASE1_ORACLE,
    min_block_production: float = DEFAULT_MIN_RESONANCE_BLOCK_PRODUCTION,
    min_r_env: float = DEFAULT_MIN_R_ENV_BLOCK_PRODUCTION,
    min_governance: float = DEFAULT_MIN_RESONANCE_GOVERNANCE,
    gtr_count_current_month: int | None = None,
    bond_in_slashing_dispute: bool = False,
    identity_active: bool = True,
) -> ValidatorResonanceProfile:
    """Determine PoREF validator eligibility from alignment dimensions."""
    resonance = compute_validator_resonance(dimensions)
    monthly_gtr_ok = (
        gtr_count_current_month is None or gtr_count_current_month > 0
    )
    block_eligible = (
        identity_active
        and not bond_in_slashing_dispute
        and monthly_gtr_ok
        and dimensions.r_env >= min_r_env
        and resonance >= min_block_production
    )
    return ValidatorResonanceProfile(
        validator_id=validator_id,
        validator_class=validator_class,
        resonance_score=resonance,
        dimensions=dimensions,
        eligible_for_block_production=block_eligible,
        eligible_for_governance=identity_active and resonance >= min_governance,
        scored_at=datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        scoring_profile=scoring_profile,
        gtr_count_current_month=gtr_count_current_month,
    )
