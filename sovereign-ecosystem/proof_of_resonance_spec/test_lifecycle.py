"""Tests for TP-102 validator lifecycle, block production, and slashing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proof_of_resonance_spec.block_production import (  # noqa: E402
    EPOCH_BLOCK_COUNT,
    ValidatorSetMember,
    assign_slot_leader,
    byzantine_fault_tolerance,
    finality_threshold,
    proportional_block_assignments,
    select_active_validator_set,
)
from proof_of_resonance_spec.lifecycle import (  # noqa: E402
    BondStatus,
    IdentityStatus,
    ValidatorOperationalState,
    ValidatorRegistration,
    is_eligible_for_block_production,
    suspension_action,
    validate_registration,
)
from proof_of_resonance_spec.models import ValidatorResonanceDimensions  # noqa: E402
from proof_of_resonance_spec.resonance import ComplianceInputs  # noqa: E402
from proof_of_resonance_spec.slashing import (  # noqa: E402
    SlashCondition,
    SlashEvidence,
    apply_slash_to_compliance,
    compute_bond_slash_amount,
    preliminary_slash_applies,
)


class ValidatorLifecycleTests(unittest.TestCase):
    def test_registration_requirements(self) -> None:
        ok = ValidatorRegistration(
            validator_id="did:tegal:VAL001",
            identity_tier=2,
            bond_tegals=10_000,
            baseline_gtr_days=90,
            jurisdiction="EU-DE",
            infrastructure_provider="GreenHost GmbH",
            energy_source_attestation="I-REC-2026-001",
            policy_statement_uri="https://example.org/policy.json",
        )
        self.assertEqual(validate_registration(ok), [])

        bad = ValidatorRegistration(
            validator_id="did:tegal:VAL002",
            identity_tier=1,
            bond_tegals=5_000,
            baseline_gtr_days=30,
            jurisdiction="",
            infrastructure_provider="",
            energy_source_attestation="",
            policy_statement_uri="",
        )
        self.assertGreaterEqual(len(validate_registration(bad)), 4)

    def test_block_eligibility_requires_r_env_floor(self) -> None:
        dimensions = ValidatorResonanceDimensions(
            r_env=0.15,
            r_gov=0.9,
            r_up=0.9,
            r_cmp=1.0,
        )
        state = ValidatorOperationalState(
            identity_status=IdentityStatus.ACTIVE,
            bond_status=BondStatus.ACTIVE,
            bond_tegals=10_000,
            gtr_count_current_month=2,
        )
        self.assertFalse(is_eligible_for_block_production(dimensions=dimensions, state=state))

    def test_suspension_on_low_resonance_streak(self) -> None:
        dimensions = ValidatorResonanceDimensions(
            r_env=0.5,
            r_gov=0.2,
            r_up=0.2,
            r_cmp=0.5,
        )
        state = ValidatorOperationalState(
            identity_status=IdentityStatus.ACTIVE,
            bond_status=BondStatus.ACTIVE,
            bond_tegals=10_000,
            gtr_count_current_month=1,
            consecutive_epochs_below_min_r=3,
        )
        self.assertEqual(suspension_action(state=state, dimensions=dimensions), "SUSPEND_AUTO")

    def test_revoked_identity_ejected(self) -> None:
        state = ValidatorOperationalState(
            identity_status=IdentityStatus.REVOKED,
            bond_status=BondStatus.ACTIVE,
            bond_tegals=10_000,
            gtr_count_current_month=1,
        )
        dimensions = ValidatorResonanceDimensions(0.8, 0.8, 0.8, 1.0)
        self.assertEqual(
            suspension_action(state=state, dimensions=dimensions),
            "EJECT_PERMANENT",
        )


class BlockProductionTests(unittest.TestCase):
    def test_validator_set_cap_and_bft(self) -> None:
        eligible = [
            ValidatorSetMember(f"did:tegal:V{i}", 1.0 - i * 0.01)
            for i in range(150)
        ]
        active = select_active_validator_set(eligible, epoch_index=1)
        self.assertEqual(len(active.members), 100)
        self.assertEqual(active.max_byzantine, byzantine_fault_tolerance(100))
        self.assertEqual(active.finality_threshold, finality_threshold(100))
        self.assertEqual(active.finality_threshold, 67)

    def test_proportional_assignments_sum_to_epoch(self) -> None:
        active = select_active_validator_set(
            [
                ValidatorSetMember("did:tegal:A", 0.8),
                ValidatorSetMember("did:tegal:B", 0.2),
            ],
            epoch_index=2,
        )
        assignments = proportional_block_assignments(active, epoch_blocks=EPOCH_BLOCK_COUNT)
        self.assertEqual(sum(assignments.values()), EPOCH_BLOCK_COUNT)
        self.assertGreater(assignments["did:tegal:A"], assignments["did:tegal:B"])

    def test_vrf_leader_is_deterministic(self) -> None:
        active = select_active_validator_set(
            [ValidatorSetMember("did:tegal:A", 0.6), ValidatorSetMember("did:tegal:B", 0.4)],
            epoch_index=3,
        )
        leader_a = assign_slot_leader(
            active,
            previous_epoch_final_block_hash="abc123",
            slot_index=7,
        )
        leader_b = assign_slot_leader(
            active,
            previous_epoch_final_block_hash="abc123",
            slot_index=7,
        )
        self.assertEqual(leader_a, leader_b)
        self.assertIn(leader_a, {"did:tegal:A", "did:tegal:B"})


class SlashingTests(unittest.TestCase):
    def test_bond_slash_amounts(self) -> None:
        self.assertEqual(
            compute_bond_slash_amount(10_000, SlashCondition.PROVABLE_DOUBLE_SIGNING),
            1_000,
        )
        self.assertEqual(
            compute_bond_slash_amount(10_000, SlashCondition.FABRICATED_GTR),
            2_000,
        )

    def test_fabricated_gtr_permanent_cmp_and_ejection(self) -> None:
        r_cmp, eject = apply_slash_to_compliance(
            ComplianceInputs(offences=(), epochs_since_last_offence=0),
            SlashCondition.FABRICATED_GTR,
        )
        self.assertEqual(r_cmp, 0.0)
        self.assertTrue(eject)

    def test_slash_evidence_triggers_preliminary_slash(self) -> None:
        evidence = SlashEvidence(
            validator_id="did:tegal:BAD",
            condition=SlashCondition.PROVABLE_DOUBLE_SIGNING,
            proof="conflicting-header-proof",
            block_heights=(100, 101),
            timestamps=("2026-07-01T00:00:00Z", "2026-07-01T00:00:01Z"),
        )
        self.assertTrue(preliminary_slash_applies(evidence))


if __name__ == "__main__":
    unittest.main()
