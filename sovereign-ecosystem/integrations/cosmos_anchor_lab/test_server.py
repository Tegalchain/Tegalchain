"""Tests for lab Cosmos anchor server."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from integrations.cosmos_anchor_lab.server import app  # noqa: E402
from tegalchain.endorsement import ORACLE_PEER_ID, Endorsement, attach_endorsements  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter.backends import SubmitterBackend  # noqa: E402
from tegalchain.submitter.config import SubmitterConfig  # noqa: E402
from tegalchain.submitter.drain import drain_queue  # noqa: E402


def _candidate(**extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "type": "TELEMETRY_MINT",
        "signer": "addr",
        "timestamp": 1,
        "on_chain_anchor": {
            "type": "GTR_ANCHOR",
            "gtr_id": "550e8400-e29b-41d4-a716-446655440030",
            "content_hash": "d" * 64,
            "attester_ids": ["n1"],
            "measurement_type": "CUSTOM",
            "timestamp": "2026-07-28T12:00:00Z",
        },
    }
    base.update(extra)
    return attach_endorsements(
        base,
        [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="cosmos-hash")],
    )


class CosmosAnchorLabTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_anchor_returns_txhash_not_labmock(self) -> None:
        candidate = _candidate()
        response = self.client.post(
            "/tegalchain/gretelemetry/v1/anchor",
            json={
                "type": "TELEMETRY_MINT",
                "block_candidate": candidate,
                "on_chain_anchor": candidate["on_chain_anchor"],
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("txhash", body)
        self.assertEqual(len(body["txhash"]), 64)
        self.assertFalse(body["txhash"].startswith("LABMOCK"))


class CosmosDrainIntegrationTests(unittest.TestCase):
    def test_drain_cosmos_backend_uses_txhash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MintQueueStore(Path(tmp) / "mint_queue.db")
            store.enqueue(
                telemetry_hash="cosmos-drain-hash",
                gtr_id="550e8400-e29b-41d4-a716-446655440030",
                block_candidate=_candidate(),
                state_update={"telemetry_hash": "cosmos-drain-hash"},
                identity={"node_id": "n1"},
            )

            lab = TestClient(app)

            from tegalchain.submitter import submit as submit_mod

            def _lab_submit(
                block_candidate: dict,
                *,
                rest_url: str,
                anchor_path: str,
                bearer_token: str | None = None,
                timeout_seconds: float = 30.0,
            ) -> str:
                path = anchor_path if anchor_path.startswith("/") else f"/{anchor_path}"
                anchor = block_candidate.get("on_chain_anchor") or {}
                resp = lab.post(
                    path,
                    json={
                        "type": "TELEMETRY_MINT",
                        "block_candidate": block_candidate,
                        "on_chain_anchor": anchor,
                    },
                )
                resp.raise_for_status()
                return str(resp.json()["txhash"])

            original = submit_mod.submit_to_cosmos
            submit_mod.submit_to_cosmos = _lab_submit
            try:
                    config = SubmitterConfig(
                        db_path=store.db_path,
                        outbox_dir=Path(tmp) / "outbox",
                        backend=SubmitterBackend.COSMOS,
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
            finally:
                submit_mod.submit_to_cosmos = original

            self.assertEqual(result.submitted, 1)
            row = store.fetch_by_id(1)
            assert row is not None
            self.assertEqual(row.status, "submitted")
            self.assertFalse(str(row.submit_ref).startswith("LABMOCK-"))
            self.assertEqual(len(str(row.submit_ref)), 64)


if __name__ == "__main__":
    unittest.main()
