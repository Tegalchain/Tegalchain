"""Tests for SQLite mint queue (Phase 1c)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from tegalchain.endorsement import ORACLE_PEER_ID, attach_endorsements, Endorsement  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter import SubmitterConfig, drain_queue  # noqa: E402
from tegalchain.submitter.backends import SubmitterBackend  # noqa: E402


def _endorsed_candidate(**extra: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "type": "TELEMETRY_MINT",
        "signer": "addr",
        "timestamp": 1,
    }
    candidate.update(extra)
    return attach_endorsements(
        candidate,
        [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="test-hash")],
    )


class MintQueueStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MintQueueStore(Path(self.tmp.name) / "mint_queue.db")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_fetch_by_gtr_id(self) -> None:
        candidate = _endorsed_candidate(gtr_id="550e8400-e29b-41d4-a716-446655440000")
        self.store.enqueue(
            telemetry_hash="gtr-hash-1",
            gtr_id="550e8400-e29b-41d4-a716-446655440000",
            block_candidate=candidate,
            state_update={"telemetry_hash": "gtr-hash-1"},
            identity={"node_id": "n1"},
        )
        row = self.store.fetch_by_gtr_id("550e8400-e29b-41d4-a716-446655440000")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.gtr_id, "550e8400-e29b-41d4-a716-446655440000")

    def test_enqueue_and_stats(self) -> None:
        queue_id = self.store.enqueue(
            telemetry_hash="abc123",
            block_candidate=_endorsed_candidate(),
            state_update={"telemetry_hash": "abc123"},
            identity={"node_id": "n1"},
        )
        self.assertEqual(queue_id, 1)
        stats = self.store.stats()
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["total"], 1)

    def test_dedupe_by_telemetry_hash(self) -> None:
        kwargs = {
            "telemetry_hash": "same-hash",
            "block_candidate": _endorsed_candidate(v=1),
            "state_update": {"telemetry_hash": "same-hash"},
            "identity": {"node_id": "n1"},
        }
        first = self.store.enqueue(**kwargs)
        kwargs["block_candidate"] = _endorsed_candidate(v=2)
        second = self.store.enqueue(**kwargs)
        self.assertEqual(first, second)
        self.assertEqual(self.store.stats()["total"], 1)

    def test_drain_outbox_without_privkey(self) -> None:
        self.store.enqueue(
            telemetry_hash="drain-me",
            block_candidate=_endorsed_candidate(
                telemetry_hash="drain-me",
                on_chain_anchor={
                    "type": "GTR_ANCHOR",
                    "gtr_id": "550e8400-e29b-41d4-a716-446655440001",
                    "content_hash": "a" * 64,
                    "attester_ids": ["n1"],
                    "measurement_type": "ENERGY_KWH",
                    "timestamp": "2026-07-26T12:00:00Z",
                },
            ),
            state_update={"telemetry_hash": "drain-me"},
            identity={"node_id": "n1"},
        )
        outbox = Path(self.tmp.name) / "outbox"
        config = SubmitterConfig(
            db_path=self.store.db_path,
            outbox_dir=outbox,
            backend=SubmitterBackend.OUTBOX,
            api_url="http://localhost:12391",
            privkey=None,
            qortal_service="99",
            qortal_data_type="JSON",
            tx_pl_path=Path("/nonexistent/tx.pl"),
            cosmos_rest_url="http://localhost:1317",
            cosmos_anchor_path="/tegalchain/gretelemetry/v1/anchor",
            cosmos_bearer_token=None,
        )
        result = drain_queue(self.store, config, limit=10)
        self.assertEqual(result.processed, 1)
        self.assertEqual(result.outboxed, 1)
        self.assertEqual(result.submitted, 0)
        self.assertEqual(self.store.stats()["outboxed"], 1)
        outbox_files = list(outbox.glob("*.json"))
        self.assertTrue(outbox_files)
        payload = json.loads(outbox_files[0].read_text(encoding="utf-8"))
        anchor = payload["block_candidate"]["on_chain_anchor"]
        self.assertIsNotNone(anchor.get("anchor_timestamp"))


if __name__ == "__main__":
    unittest.main()
