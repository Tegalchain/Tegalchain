"""Tests for deterministic finality helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.endorsement import ORACLE_PEER_ID, Endorsement, attach_endorsements  # noqa: E402
from tegalchain.finality import (  # noqa: E402
    FinalityError,
    FinalityProof,
    assert_no_reorg,
    finality_proof_from_queue_record,
    is_finalized_status,
)
from tegalchain.queue.store import MintQueueStore  # noqa: E402


class FinalityTests(unittest.TestCase):
    def test_is_finalized_status(self) -> None:
        self.assertTrue(is_finalized_status("submitted"))
        self.assertFalse(is_finalized_status("pending"))
        self.assertFalse(is_finalized_status("outboxed"))

    def test_finality_proof_from_submitted_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MintQueueStore(Path(tmp) / "mint_queue.db")
            queue_id = store.enqueue(
                telemetry_hash="hash-final",
                block_candidate=attach_endorsements(
                    {"type": "TELEMETRY_MINT"},
                    [Endorsement(peer=ORACLE_PEER_ID)],
                ),
                state_update={"telemetry_hash": "hash-final"},
                identity={"node_id": "n1"},
            )
            store.mark_submitted(queue_id, "chain-signature-xyz")
            record = store.fetch_by_id(queue_id)
            assert record is not None
            proof = finality_proof_from_queue_record(record)
            self.assertIsInstance(proof, FinalityProof)
            self.assertTrue(proof.irreversible)
            self.assertEqual(proof.submit_ref, "chain-signature-xyz")
            self.assertEqual(proof.telemetry_hash, "hash-final")

    def test_pending_record_not_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MintQueueStore(Path(tmp) / "mint_queue.db")
            queue_id = store.enqueue(
                telemetry_hash="pending-hash",
                block_candidate={"type": "TELEMETRY_MINT"},
                state_update={},
                identity={},
            )
            record = store.fetch_by_id(queue_id)
            assert record is not None
            with self.assertRaises(FinalityError):
                finality_proof_from_queue_record(record)

    def test_assert_no_reorg(self) -> None:
        assert_no_reorg("sig-a", "sig-a")
        with self.assertRaises(FinalityError):
            assert_no_reorg("sig-a", "sig-b")


if __name__ == "__main__":
    unittest.main()
