"""Tests for TP-103 GreenLedger archival on submit."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.auditrail import correlate_submitted_record  # noqa: E402
from tegalchain.endorsement import ORACLE_PEER_ID, Endorsement, attach_endorsements  # noqa: E402
from tegalchain.greenledger import archive_submitted_gtr  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402


def _submitted_candidate() -> dict[str, object]:
    base: dict[str, object] = {
        "type": "TELEMETRY_MINT",
        "gtr_id": "550e8400-e29b-41d4-a716-446655440030",
        "gtr_hash": "e" * 64,
        "auditrail_record_type": "GREETELEMETRY",
        "tp101_record": {
            "gtr_id": "550e8400-e29b-41d4-a716-446655440030",
            "source_id": "gle-node-1",
            "measurement_type": "CUSTOM",
            "value": 1024.0,
            "unit": "bytes",
            "timestamp": "2026-07-26T10:00:00Z",
            "attestations": [
                {
                    "attester_id": "did:tegal:GLE001",
                    "attester_type": "DEVICE",
                    "signature": "f" * 128,
                    "timestamp": "2026-07-26T10:00:01Z",
                }
            ],
        },
        "on_chain_anchor": {
            "type": "GTR_ANCHOR",
            "gtr_id": "550e8400-e29b-41d4-a716-446655440030",
            "content_hash": "e" * 64,
            "anchor_timestamp": "2026-07-26T10:00:05Z",
        },
    }
    return attach_endorsements(
        base,
        [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="gle-hash")],
    )


class GreenLedgerArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MintQueueStore(Path(self.tmp.name) / "mint_queue.db")
        self.candidate = _submitted_candidate()
        self.queue_id = self.store.enqueue(
            telemetry_hash="gle-hash",
            gtr_id="550e8400-e29b-41d4-a716-446655440030",
            block_candidate=self.candidate,
            state_update={"telemetry_hash": "gle-hash"},
            identity={"node_id": "gle-node-1"},
        )
        self.store.mark_submitted(
            self.queue_id,
            "LABMOCK-GLEARCHIVE001",
            block_candidate=self.candidate,
        )
        self.record = self.store.fetch_by_id(self.queue_id)
        assert self.record is not None

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_archive_submitted_gtr(self) -> None:
        gle = archive_submitted_gtr(
            self.store,
            self.record,
            block_candidate=self.candidate,
        )
        self.assertEqual(gle.gtr_id, "550e8400-e29b-41d4-a716-446655440030")
        self.assertEqual(gle.ledger_ref, "LABMOCK-GLEARCHIVE001")
        stored = self.store.fetch_greenledger_by_gtr_id(gle.gtr_id)
        assert stored is not None
        self.assertEqual(stored["gle_id"], gle.gle_id)
        self.assertEqual(stored["source_id"], "gle-node-1")

    def test_correlate_also_archives_gle(self) -> None:
        correlate_submitted_record(
            self.store,
            self.record,
            block_candidate=self.candidate,
        )
        gle = self.store.fetch_greenledger_by_gtr_id(
            "550e8400-e29b-41d4-a716-446655440030"
        )
        assert gle is not None
        self.assertEqual(gle["protocol_standard"], "TP-103")

    def test_archive_refreshes_carbon_account(self) -> None:
        archive_submitted_gtr(
            self.store,
            self.record,
            block_candidate=self.candidate,
        )
        account = self.store.fetch_latest_carbon_account("gle-node-1")
        assert account is not None
        self.assertEqual(account["source_id"], "gle-node-1")
        self.assertEqual(account["protocol_standard"], "TP-103")

    def test_query_by_source_id(self) -> None:
        archive_submitted_gtr(
            self.store,
            self.record,
            block_candidate=self.candidate,
        )
        rows = self.store.query_greenledger(source_id="gle-node-1", limit=10)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
