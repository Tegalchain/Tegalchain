"""Tests for Tegalchain client application wrappers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.client import (  # noqa: E402
    GreTelemetryProducerClient,
    OrderingClient,
    QueryClient,
)
from tegalchain.endorsement import (  # noqa: E402
    ORACLE_PEER_ID,
    Endorsement,
    attach_endorsements,
)
from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter.config import SubmitterConfig  # noqa: E402
from tegalchain.submitter.backends import SubmitterBackend  # noqa: E402


class ClientApplicationTests(unittest.TestCase):
    def test_producer_client_delegates_to_submit_telemetry(self) -> None:
        client = GreTelemetryProducerClient("http://127.0.0.1:8090")
        with patch("tegalchain.client.submit_telemetry", return_value={"ok": True}) as mock:
            result = client.propose_and_endorse({"node_id": "n1"})
        mock.assert_called_once_with("http://127.0.0.1:8090", {"node_id": "n1"})
        self.assertEqual(result, {"ok": True})

    def test_ordering_client_drains_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "mint_queue.db"
            outbox = Path(tmp) / "outbox"
            store = MintQueueStore(db)
            store.enqueue(
                telemetry_hash="hash1",
                block_candidate=attach_endorsements(
                    {"type": "TELEMETRY_MINT", "signer": "addr", "timestamp": 1},
                    [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="hash1")],
                ),
                state_update={"telemetry_hash": "hash1"},
                identity={"node_id": "n1"},
            )
            config = SubmitterConfig(
                db_path=db,
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
            client = OrderingClient(config)
            result = client.submit_to_ordering(limit=5)
            self.assertEqual(result.processed, 1)
            self.assertEqual(result.outboxed, 1)

    def test_query_client_peer_state_not_implemented(self) -> None:
        client = QueryClient()
        with self.assertRaises(NotImplementedError):
            client.query_peer_state("node:zeegate:n1")


if __name__ == "__main__":
    unittest.main()
