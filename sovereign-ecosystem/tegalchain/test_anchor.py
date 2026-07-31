"""Tests for TP-101 on-chain GTR anchor and Merkle batching."""

from __future__ import annotations

import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import AttesterType, MeasurementType  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from tegalchain.anchor import (  # noqa: E402
    build_merkle_batch_anchors,
    build_on_chain_anchor,
    finalize_anchor_for_submit,
    merkle_batch_recommended,
)
from tegalchain.block import verify_merkle_proof  # noqa: E402


class GtrAnchorTests(unittest.TestCase):
    def test_on_chain_anchor_excludes_full_gtr(self) -> None:
        record = build_signed_tp101_gtr(
            source_id="bytenergy-node-1",
            source_type=__import__(
                "greentelemetry_protocol_spec.models", fromlist=["SourceType"]
            ).SourceType.SENSOR,
            measurement_type=MeasurementType.ENERGY_KWH,
            value=3.5,
            unit="kWh",
            gtr_id=str(uuid.uuid4()),
            attester_type=AttesterType.DEVICE,
        )
        anchor = build_on_chain_anchor(record)
        payload = anchor.to_dict()
        self.assertEqual(payload["type"], "GTR_ANCHOR")
        self.assertEqual(payload["gtr_id"], record.gtr_id)
        self.assertEqual(len(payload["content_hash"]), 64)
        self.assertEqual(payload["attester_ids"], [record.source_id])
        self.assertEqual(payload["measurement_type"], "ENERGY_KWH")
        self.assertEqual(payload["timestamp"], record.timestamp)
        self.assertNotIn("value", payload)
        self.assertNotIn("metadata", payload)

    def test_finalize_sets_anchor_timestamp(self) -> None:
        record = build_signed_tp101_gtr(
            source_id="bytenergy-node-1",
            source_type=__import__(
                "greentelemetry_protocol_spec.models", fromlist=["SourceType"]
            ).SourceType.SENSOR,
            measurement_type=MeasurementType.ENERGY_KWH,
            value=1.0,
            unit="kWh",
            attester_type=AttesterType.DEVICE,
        )
        anchor = build_on_chain_anchor(record)
        self.assertIsNone(anchor.anchor_timestamp)
        finalized = finalize_anchor_for_submit(anchor)
        self.assertIsNotNone(finalized.anchor_timestamp)
        self.assertTrue(finalized.anchor_timestamp.endswith("Z"))

    def test_merkle_batch_proofs_verify_against_root(self) -> None:
        anchors = []
        leaves: list[str] = []
        for index in range(4):
            record = build_signed_tp101_gtr(
                source_id=f"bytenergy-node-{index}",
                source_type=__import__(
                    "greentelemetry_protocol_spec.models", fromlist=["SourceType"]
                ).SourceType.SENSOR,
                measurement_type=MeasurementType.ENERGY_KWH,
                value=float(index + 1),
                unit="kWh",
                gtr_id=str(uuid.uuid4()),
                attester_type=AttesterType.DEVICE,
            )
            anchor = build_on_chain_anchor(record)
            anchors.append(anchor)
            leaves.append(anchor.content_hash)

        batch = build_merkle_batch_anchors(anchors, anchor_timestamp="2026-07-26T12:00:00Z")
        self.assertEqual(batch.record_count, 4)
        self.assertEqual(batch.anchor_timestamp, "2026-07-26T12:00:00Z")
        for index, anchor in enumerate(anchors):
            proof = batch.proofs[anchor.gtr_id]
            self.assertTrue(
                verify_merkle_proof(anchor.content_hash, proof, batch.merkle_root, index)
            )

    def test_merkle_batch_recommended_threshold(self) -> None:
        self.assertFalse(merkle_batch_recommended(50.0))
        self.assertTrue(merkle_batch_recommended(150.0))


if __name__ == "__main__":
    unittest.main()
