"""Unit tests for mint worker ingest pipeline (no HTTP)."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import Metrics, SovereignNodeTelemetry, SystemType  # noqa: E402
from greentelemetry_protocol_spec.models import MeasurementType, SourceType  # noqa: E402
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from integrations.mint_worker.ingest import ingest_payload, record_to_api_response  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402


def _signed_legacy() -> dict:
    unsigned = SovereignNodeTelemetry(
        node_id="ingest-node-1",
        timestamp=int(time.time()),
        system_type=SystemType.ZEEGATE_TELECOM,
        metrics=Metrics(telecom_bandwidth_bytes=512),
        signature="",
    )
    payload = unsigned.to_dict()
    payload["signature"] = sign_payload(unsigned_canonical_json(payload))
    return payload


LAB_EDGE_HMAC = bytes.fromhex("736f7665726569676e2d6c61622d686d61632d7365637265743031")


def _signed_cdr_style_gtr() -> dict:
    record = build_signed_tp101_gtr(
        source_id="did:tegal:LABEDGE001",
        source_type=SourceType.API,
        measurement_type=MeasurementType.CUSTOM,
        value=12288.0,
        unit="bytes",
        metadata={"system_type": "ZEEGATE_TELECOM", "evidence_kind": "CDR"},
        project_id="zeegate-telecom",
        binding_id="edge-sim-01",
        signing_secret=LAB_EDGE_HMAC,
    )
    return record.to_dict()


class IngestPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "dev"
        self.store = MintQueueStore(Path(self.tmp.name) / "mint_queue.db")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ingest_returns_gtr_id(self) -> None:
        result = ingest_payload(self.store, _signed_legacy())
        self.assertTrue(result.gtr_id)
        self.assertEqual(result.status, "pending")
        self.assertIsNone(result.ledger_ref)
        row = self.store.fetch_by_gtr_id(result.gtr_id)
        self.assertIsNotNone(row)

    def test_ingest_cdr_style_gtr_in_dev_mode(self) -> None:
        """CDR adapter signs with tegalid binding secret even when worker is in dev mode."""
        result = ingest_payload(self.store, _signed_cdr_style_gtr())
        self.assertTrue(result.gtr_id)
        self.assertEqual(result.status, "pending")

    def test_record_api_shape(self) -> None:
        result = ingest_payload(self.store, _signed_legacy())
        row = self.store.fetch_by_gtr_id(result.gtr_id)
        assert row is not None
        api = record_to_api_response(row)
        self.assertEqual(api["gtr_id"], result.gtr_id)
        self.assertIn("attestations", api)
        self.assertIn("on_chain_anchor", api)

    def test_ingest_embeds_on_chain_anchor(self) -> None:
        result = ingest_payload(self.store, _signed_legacy())
        anchor = result.on_chain_anchor
        self.assertEqual(anchor["type"], "GTR_ANCHOR")
        self.assertEqual(anchor["gtr_id"], result.gtr_id)
        self.assertIn("content_hash", anchor)
        self.assertIn("accepted_at", result.block_candidate)

    def test_source_rate_limit(self) -> None:
        for _ in range(3):
            ingest_payload(self.store, _signed_legacy())
        with self.assertRaises(Exception) as ctx:
            self.store.check_and_increment_source_rate("ingest-node-1", max_per_hour=3)
        self.assertIn("rate limit", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
