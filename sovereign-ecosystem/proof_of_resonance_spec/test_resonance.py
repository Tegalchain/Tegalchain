"""Tests for TP-102 validator Resonance Score (R) dimensions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proof_of_resonance_spec.eligibility import score_validator, score_validator_dimensions  # noqa: E402
from proof_of_resonance_spec.models import ValidatorClass, ValidatorResonanceDimensions  # noqa: E402
from proof_of_resonance_spec.resonance import (  # noqa: E402
    ComplianceInputs,
    ComplianceOffence,
    EnvironmentalInputs,
    GovernanceInputs,
    UptimeInputs,
    compute_r_cmp,
    compute_r_env,
    compute_r_gov,
    compute_r_up,
    compute_latency_factor,
    compute_resonance_score,
)
from proof_of_resonance_spec.validate import validate_por_payload  # noqa: E402


class ResonanceDimensionTests(unittest.TestCase):
    def test_r_env_zero_without_monthly_gtr(self) -> None:
        inputs = EnvironmentalInputs(
            gtr_count_current_month=0,
            carbon_intensity_kwh_per_block=0.5,
            network_median_carbon_intensity=1.0,
            renewable_ratio=1.0,
            offset_coverage=1.0,
        )
        self.assertEqual(compute_r_env(inputs), 0.0)

    def test_r_env_from_green_telemetry(self) -> None:
        inputs = EnvironmentalInputs(
            gtr_count_current_month=2,
            carbon_intensity_kwh_per_block=0.5,
            network_median_carbon_intensity=1.0,
            renewable_ratio=0.8,
            offset_coverage=0.6,
        )
        score = compute_r_env(inputs)
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_r_gov_abstention_penalty(self) -> None:
        base = GovernanceInputs(
            vote_participation_rate=0.9,
            policy_consistency_rate=0.9,
            proposal_acceptance_rate=0.8,
            abstention_rate=0.2,
        )
        penalized = GovernanceInputs(
            vote_participation_rate=0.9,
            policy_consistency_rate=0.9,
            proposal_acceptance_rate=0.8,
            abstention_rate=0.5,
        )
        self.assertGreater(compute_r_gov(base), compute_r_gov(penalized))

    def test_r_up_latency_decay(self) -> None:
        self.assertEqual(
            compute_latency_factor(100.0, network_median_ms=100.0, network_p95_ms=200.0),
            1.0,
        )
        self.assertEqual(
            compute_latency_factor(200.0, network_median_ms=100.0, network_p95_ms=200.0),
            0.5,
        )
        inputs = UptimeInputs(
            blocks_produced=9,
            blocks_assigned=10,
            propagation_time_ms=100.0,
            network_median_propagation_ms=100.0,
            network_p95_propagation_ms=200.0,
        )
        self.assertAlmostEqual(compute_r_up(inputs), 0.9, places=4)

    def test_r_cmp_slashing_and_decay(self) -> None:
        slashed = ComplianceInputs(
            offences=(ComplianceOffence.DOUBLE_SIGNING,),
            epochs_since_last_offence=0,
        )
        self.assertAlmostEqual(compute_r_cmp(slashed), 0.6, places=4)
        recovered = ComplianceInputs(offences=(), epochs_since_last_offence=5)
        self.assertGreater(compute_r_cmp(recovered), 0.99)

    def test_composite_resonance_formula(self) -> None:
        score = compute_resonance_score(0.8, 0.7, 0.9, 1.0)
        expected = 0.30 * 0.8 + 0.25 * 0.7 + 0.25 * 0.9 + 0.20 * 1.0
        self.assertAlmostEqual(score, round(expected, 4), places=4)


class ValidatorEligibilityTests(unittest.TestCase):
    def test_block_production_requires_monthly_gtr(self) -> None:
        dimensions = ValidatorResonanceDimensions(
            r_env=0.0,
            r_gov=0.9,
            r_up=0.9,
            r_cmp=1.0,
        )
        profile = score_validator(
            validator_id="did:tegal:VALIDATOR001",
            validator_class=ValidatorClass.ENERGY,
            dimensions=dimensions,
            gtr_count_current_month=0,
        )
        self.assertFalse(profile.eligible_for_block_production)
        validate_por_payload(profile.to_dict())

    def test_high_alignment_eligible_for_blocks(self) -> None:
        dimensions = score_validator_dimensions(
            environmental=EnvironmentalInputs(
                gtr_count_current_month=3,
                carbon_intensity_kwh_per_block=0.4,
                network_median_carbon_intensity=1.0,
                renewable_ratio=0.95,
                offset_coverage=0.8,
            ),
            governance=GovernanceInputs(
                vote_participation_rate=0.95,
                policy_consistency_rate=0.9,
                proposal_acceptance_rate=0.85,
                abstention_rate=0.1,
            ),
            uptime=UptimeInputs(
                blocks_produced=98,
                blocks_assigned=100,
                propagation_time_ms=100.0,
                network_median_propagation_ms=100.0,
                network_p95_propagation_ms=200.0,
            ),
            compliance=ComplianceInputs(offences=(), epochs_since_last_offence=3),
        )
        profile = score_validator(
            validator_id="did:tegal:VALIDATOR002",
            validator_class=ValidatorClass.ENERGY,
            dimensions=dimensions,
            gtr_count_current_month=3,
        )
        self.assertGreaterEqual(profile.resonance_score, 0.40)
        self.assertTrue(profile.eligible_for_block_production)
        validate_por_payload(profile.to_dict())


    def test_r_env_floor_blocks_eligibility(self) -> None:
        dimensions = ValidatorResonanceDimensions(
            r_env=0.10,
            r_gov=0.9,
            r_up=0.9,
            r_cmp=1.0,
        )
        profile = score_validator(
            validator_id="did:tegal:LOWENV",
            validator_class=ValidatorClass.ENERGY,
            dimensions=dimensions,
            gtr_count_current_month=2,
        )
        self.assertFalse(profile.eligible_for_block_production)


if __name__ == "__main__":
    unittest.main()
