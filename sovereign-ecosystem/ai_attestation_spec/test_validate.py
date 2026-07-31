"""Tests for TP-108 schema validation."""

from __future__ import annotations

import unittest

from ai_attestation_spec.validate import (
    AiAttestationValidationError,
    canonical_inputs_hash,
    validate_tp108_metadata,
)


class TestTp108Validate(unittest.TestCase):
    def test_valid_corroboration_metadata(self) -> None:
        validate_tp108_metadata(
            {
                "protocol_standard": "TP-108",
                "schema_version": "1.0.0",
                "claim_type": "CORROBORATION",
                "model_profile": "zeegate-cdr-bandwidth-v1",
                "inputs_hash": "a" * 64,
                "verdict": "PASS",
                "score": 0.91,
            }
        )

    def test_rejects_wrong_protocol_standard(self) -> None:
        with self.assertRaises(AiAttestationValidationError):
            validate_tp108_metadata(
                {
                    "protocol_standard": "TP-101",
                    "schema_version": "1.0.0",
                    "claim_type": "PLAUSIBILITY",
                    "model_profile": "test",
                    "inputs_hash": "b" * 64,
                    "verdict": "WARN",
                }
            )

    def test_canonical_inputs_hash_stable(self) -> None:
        inputs = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
        h1 = canonical_inputs_hash(inputs)
        h2 = canonical_inputs_hash({"a": 1, "b": 2, "nested": {"y": 8, "z": 9}})
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


if __name__ == "__main__":
    unittest.main()
