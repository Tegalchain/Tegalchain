"""Tests for TP-103 Auditrail correlation after chain submit."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.auditrail import build_auditrail_correlation, correlate_submitted_record  # noqa: E402
from tegalchain.endorsement import ORACLE_PEER_ID, Endorsement, attach_endorsements  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402


def _submitted_candidate() -> dict[str, object]:
    base: dict[str, object] = {
        "type": "TELEMETRY_MINT",
        "signer": "addr",
        "timestamp": 1,
        "gtr_id": "550e8400-e29b-41d4-a716-446655440010",
        "auditrail_record_type": "GREETELEMETRY",
        "tegalid_did": "did:tegal:LABEDGE001",
        "project_id": "proj-1",
        "binding_id": "bind-1",
        "tp101_record": {
            "gtr_id": "550e8400-e29b-41d4-a716-446655440010",
            "source_id": "did:tegal:LABEDGE001",
            "measurement_type": "CUSTOM",
            "value": 512.0,
            "unit": "bytes",
            "timestamp": "2026-07-26T12:00:00Z",
            "project_id": "proj-1",
            "binding_id": "bind-1",
            "attestations": [
                {
                    "attester_id": "did:tegal:LABEDGE001",
                    "attester_type": "DEVICE",
                    "signature": "a" * 128,
                    "timestamp": "2026-07-26T12:00:01Z",
                }
            ],
        },
        "on_chain_anchor": {
            "type": "GTR_ANCHOR",
            "gtr_id": "550e8400-e29b-41d4-a716-446655440010",
            "content_hash": "b" * 64,
            "attester_ids": ["did:tegal:LABEDGE001"],
            "measurement_type": "CUSTOM",
            "timestamp": "2026-07-26T12:00:00Z",
            "anchor_timestamp": "2026-07-26T12:00:05Z",
        },
    }
    return attach_endorsements(
        base,
        [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="audit-hash")],
    )


class AuditrailCorrelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MintQueueStore(Path(self.tmp.name) / "mint_queue.db")
        self.candidate = _submitted_candidate()
        self.queue_id = self.store.enqueue(
            telemetry_hash="audit-hash",
            gtr_id="550e8400-e29b-41d4-a716-446655440010",
            block_candidate=self.candidate,
            state_update={"telemetry_hash": "audit-hash"},
            identity={"node_id": "did:tegal:LABEDGE001"},
        )
        self.store.mark_submitted(
            self.queue_id,
            "QORTAL_SIG_123",
            block_candidate=self.candidate,
        )
        self.record = self.store.fetch_by_id(self.queue_id)
        assert self.record is not None

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_build_correlation_fields(self) -> None:
        correlation = build_auditrail_correlation(
            self.record,
            block_candidate=self.candidate,
        )
        self.assertEqual(correlation.gtr_id, "550e8400-e29b-41d4-a716-446655440010")
        self.assertEqual(correlation.submit_ref, "QORTAL_SIG_123")
        self.assertEqual(correlation.content_hash, "b" * 64)
        self.assertEqual(correlation.auditrail_record_type, "GREETELEMETRY")
        self.assertEqual(correlation.project_id, "proj-1")

    def test_persist_and_fetch_correlation(self) -> None:
        correlate_submitted_record(
            self.store,
            self.record,
            block_candidate=self.candidate,
        )
        stored = self.store.fetch_auditrail_by_gtr_id(
            "550e8400-e29b-41d4-a716-446655440010"
        )
        assert stored is not None
        self.assertEqual(stored["submit_ref"], "QORTAL_SIG_123")
        self.assertEqual(stored["anchor_timestamp"], "2026-07-26T12:00:05Z")
        gle = self.store.fetch_greenledger_by_gtr_id(
            "550e8400-e29b-41d4-a716-446655440010"
        )
        assert gle is not None
        self.assertEqual(gle["protocol_standard"], "TP-103")


if __name__ == "__main__":
    unittest.main()
