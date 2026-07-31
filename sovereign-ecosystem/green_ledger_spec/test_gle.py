"""Tests for TP-103 GreenLedger Entry (GLE) builder."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from green_ledger_spec.gle import build_greenledger_entry  # noqa: E402
from green_ledger_spec.models import RetentionClass  # noqa: E402
from green_ledger_spec.retention import is_within_retention, retention_expires_at  # noqa: E402
from green_ledger_spec.validate import validate_gle_payload  # noqa: E402


def _block_candidate() -> dict[str, object]:
    return {
        "gtr_id": "550e8400-e29b-41d4-a716-446655440020",
        "gtr_hash": "c" * 64,
        "tp101_record": {
            "gtr_id": "550e8400-e29b-41d4-a716-446655440020",
            "source_id": "sensor-east-01",
            "measurement_type": "ENERGY_KWH",
            "value": 42.5,
            "unit": "kWh",
            "timestamp": "2026-07-26T11:00:00Z",
            "attestations": [
                {
                    "attester_id": "did:tegal:DEVICE001",
                    "attester_type": "DEVICE",
                    "signature": "a" * 128,
                    "timestamp": "2026-07-26T11:00:01Z",
                    "confidence": 0.95,
                }
            ],
        },
        "on_chain_anchor": {
            "type": "GTR_ANCHOR",
            "gtr_id": "550e8400-e29b-41d4-a716-446655440020",
            "content_hash": "c" * 64,
            "anchor_timestamp": "2026-07-26T12:00:05Z",
        },
    }


class GleBuilderTests(unittest.TestCase):
    def test_build_and_validate_gle(self) -> None:
        gle = build_greenledger_entry(
            block_candidate=_block_candidate(),
            ledger_ref="LABMOCK-ABC123",
            archive_timestamp="2026-07-26T12:00:10Z",
        )
        payload = gle.to_dict()
        validate_gle_payload(payload)
        self.assertEqual(payload["protocol_standard"], "TP-103")
        self.assertEqual(payload["gtr_id"], "550e8400-e29b-41d4-a716-446655440020")
        self.assertEqual(payload["retention_class"], "STANDARD")
        self.assertEqual(payload["attestation_count"], 1)

    def test_regulatory_retention_class(self) -> None:
        gle = build_greenledger_entry(
            block_candidate=_block_candidate(),
            ledger_ref="0x" + "d" * 64,
            retention_class=RetentionClass.REGULATORY,
            tags=("ghg-report",),
        )
        self.assertEqual(gle.retention_class, RetentionClass.REGULATORY)
        self.assertEqual(gle.tags, ("ghg-report",))

    def test_retention_window(self) -> None:
        expires = retention_expires_at("2026-01-01T00:00:00Z", RetentionClass.STANDARD)
        assert expires is not None
        self.assertTrue(
            is_within_retention(
                "2026-01-01T00:00:00Z",
                RetentionClass.STANDARD,
                now=expires,
            )
        )
        self.assertTrue(
            is_within_retention("2026-01-01T00:00:00Z", RetentionClass.PERMANENT)
        )


if __name__ == "__main__":
    unittest.main()
