"""Tests for pluggable submit backends (mock, cosmos, outbox)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from tegalchain.endorsement import ORACLE_PEER_ID, Endorsement, attach_endorsements  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter.backends import SubmitterBackend, resolve_submitter_backend  # noqa: E402
from tegalchain.submitter.config import SubmitterConfig  # noqa: E402
from tegalchain.submitter.drain import drain_queue  # noqa: E402
from tegalchain.submitter.mock import mock_submit_ref  # noqa: E402


def _candidate(**extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "type": "TELEMETRY_MINT",
        "signer": "addr",
        "timestamp": 1,
        "on_chain_anchor": {
            "type": "GTR_ANCHOR",
            "gtr_id": "550e8400-e29b-41d4-a716-446655440020",
            "content_hash": "c" * 64,
            "attester_ids": ["n1"],
            "measurement_type": "CUSTOM",
            "timestamp": "2026-07-26T12:00:00Z",
        },
    }
    base.update(extra)
    return attach_endorsements(
        base,
        [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="mock-hash")],
    )


class SubmitterBackendTests(unittest.TestCase):
    def test_mock_submit_ref_is_deterministic(self) -> None:
        payload = _candidate()
        first = mock_submit_ref(payload, queue_id=1)
        second = mock_submit_ref(payload, queue_id=1)
        self.assertTrue(first.startswith("LABMOCK-"))
        self.assertEqual(first, second)

    def test_resolve_mock_from_env(self) -> None:
        with patch.dict("os.environ", {"TEGALCHAIN_SUBMITTER_BACKEND": "mock"}, clear=False):
            self.assertEqual(resolve_submitter_backend(), SubmitterBackend.MOCK)

    def test_resolve_outbox_without_privkey(self) -> None:
        env = {k: v for k, v in __import__("os").environ.items() if k != "TEGALCHAIN_PRIVKEY"}
        env.pop("TEGALCHAIN_SUBMITTER_BACKEND", None)
        env.pop("TEGALCHAIN_COSMOS_REST_URL", None)
        with patch.dict("os.environ", env, clear=True):
            self.assertEqual(resolve_submitter_backend(privkey=None), SubmitterBackend.OUTBOX)

    def test_drain_mock_submits_and_correlates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MintQueueStore(Path(tmp) / "mint_queue.db")
            store.enqueue(
                telemetry_hash="mock-drain",
                gtr_id="550e8400-e29b-41d4-a716-446655440020",
                block_candidate=_candidate(),
                state_update={"telemetry_hash": "mock-drain"},
                identity={"node_id": "n1"},
            )
            config = SubmitterConfig(
                db_path=store.db_path,
                outbox_dir=Path(tmp) / "outbox",
                backend=SubmitterBackend.MOCK,
                api_url="http://localhost:12391",
                privkey=None,
                qortal_service="99",
                qortal_data_type="JSON",
                tx_pl_path=Path("/nonexistent/tx.pl"),
                cosmos_rest_url="http://localhost:1317",
                cosmos_anchor_path="/tegalchain/gretelemetry/v1/anchor",
                cosmos_bearer_token=None,
            )
            result = drain_queue(store, config, limit=5)
            self.assertEqual(result.submitted, 1)
            self.assertEqual(result.outboxed, 0)
            row = store.fetch_by_id(1)
            assert row is not None
            self.assertEqual(row.status, "submitted")
            self.assertTrue(str(row.submit_ref).startswith("LABMOCK-"))
            auditrail = store.fetch_auditrail_by_gtr_id(
                "550e8400-e29b-41d4-a716-446655440020"
            )
            assert auditrail is not None
            self.assertEqual(auditrail["submit_ref"], row.submit_ref)


if __name__ == "__main__":
    unittest.main()
