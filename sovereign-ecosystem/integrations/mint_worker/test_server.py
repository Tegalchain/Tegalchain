"""Tests for mint worker Phase 1 pipeline."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from greentelemetry_protocol_spec.models import Metrics, SovereignNodeTelemetry, SystemType  # noqa: E402
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from greentelemetry_protocol_spec.models import MeasurementType, SourceType  # noqa: E402
from integrations.mint_worker.server import _queue_store, app  # noqa: E402

LAB_BINDINGS = ROOT / "tegalchain" / "data" / "tegalid_bindings.example.json"
LAB_HMAC = b"sovereign-lab-hmac-secret01"


def _signed_zeegate_payload() -> dict:
    unsigned = SovereignNodeTelemetry(
        node_id="test-node-001",
        timestamp=int(time.time()),
        system_type=SystemType.ZEEGATE_TELECOM,
        metrics=Metrics(telecom_bandwidth_bytes=4096),
        signature="",
    )
    canonical = unsigned_canonical_json(unsigned.to_dict())
    return SovereignNodeTelemetry(
        node_id=unsigned.node_id,
        timestamp=unsigned.timestamp,
        system_type=unsigned.system_type,
        metrics=unsigned.metrics,
        signature=sign_payload(canonical),
    ).to_dict()


class MintWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "dev"
        os.environ.pop("TEGALCHAIN_REQUIRE_BEARER", None)
        os.environ.pop("MINT_WORKER_BEARER_TOKEN", None)
        os.environ["TEGALCHAIN_MINT_QUEUE_DB"] = str(
            Path(self.tmp.name) / "mint_queue.db"
        )
        _queue_store.cache_clear()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        _queue_store.cache_clear()
        self.tmp.cleanup()
        os.environ.pop("TEGALCHAIN_MINT_QUEUE_DB", None)
        os.environ.pop("TEGALCHAIN_IDENTITY_MODE", None)
        os.environ.pop("TEGALID_BINDINGS_FILE", None)
        os.environ.pop("TEGALCHAIN_REQUIRE_BEARER", None)
        os.environ.pop("MINT_WORKER_BEARER_TOKEN", None)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["protocol_version"], "1.3.0")
        self.assertEqual(body["identity_mode"], "dev")
        self.assertEqual(body["zk_mode"], "off")

    def test_mint_zeegate_telemetry(self) -> None:
        response = self.client.post("/v1/telemetry", json=_signed_zeegate_payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["block_candidate"]["type"], "TELEMETRY_MINT")
        self.assertIn("tegal_address", body["identity"])
        self.assertGreaterEqual(body["queue_id"], 1)
        self.assertEqual(body["gtr"]["protocol_standard"], "TP-101")
        self.assertEqual(body["gtr"]["schema_version"], "1.0")
        self.assertIn("gtr_id", body["gtr"])
        self.assertIn("TP-103", body["gtr"]["consumers"])

    def test_queue_stats_after_mint(self) -> None:
        self.client.post("/v1/telemetry", json=_signed_zeegate_payload())
        stats = self.client.get("/v1/queue/stats").json()
        self.assertEqual(stats["pending"], 1)
        self.assertEqual(stats["total"], 1)

    def test_rejects_bad_signature(self) -> None:
        payload = _signed_zeegate_payload()
        payload["signature"] = "hmac-sha256:" + "0" * 64
        response = self.client.post("/v1/telemetry", json=payload)
        self.assertEqual(response.status_code, 401)

    def test_tegalid_mode_requires_binding(self) -> None:
        tegalid_tmp = tempfile.TemporaryDirectory()
        try:
            shutil.copy(LAB_BINDINGS, Path(tegalid_tmp.name) / "bindings.json")
            os.environ["TEGALCHAIN_IDENTITY_MODE"] = "tegalid"
            os.environ["TEGALID_BINDINGS_FILE"] = str(Path(tegalid_tmp.name) / "bindings.json")
            _queue_store.cache_clear()
            client = TestClient(app)

            unsigned = {
                "node_id": "did:tegal:LABEDGE001",
                "project_id": "zeegate-telecom",
                "binding_id": "edge-sim-01",
                "timestamp": int(time.time()),
                "system_type": "ZEEGATE_TELECOM",
                "metrics": {"telecom_bandwidth_bytes": 2048},
            }
            canonical = json.dumps(unsigned, separators=(",", ":"), sort_keys=True)
            unsigned["signature"] = sign_payload(canonical, LAB_HMAC)
            response = client.post("/v1/telemetry", json=unsigned)
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertEqual(body["block_candidate"]["tegalid_did"], "did:tegal:LABEDGE001")

            bad = dict(unsigned)
            bad["node_id"] = "did:tegal:NOTREGISTERED"
            canonical = json.dumps(
                {k: v for k, v in bad.items() if k != "signature"},
                separators=(",", ":"),
                sort_keys=True,
            )
            bad["signature"] = sign_payload(canonical, LAB_HMAC)
            denied = client.post("/v1/telemetry", json=bad)
            self.assertEqual(denied.status_code, 403)
        finally:
            tegalid_tmp.cleanup()
            os.environ["TEGALCHAIN_IDENTITY_MODE"] = "dev"
            os.environ.pop("TEGALID_BINDINGS_FILE", None)
            _queue_store.cache_clear()


def _signed_gtr_v1_payload(**overrides: object) -> dict:
    record = build_signed_tp101_gtr(
        source_id="test-node-001",
        source_type=SourceType.API,
        measurement_type=MeasurementType.CUSTOM,
        value=4096.0,
        unit="bytes",
        metadata={"system_type": "ZEEGATE_TELECOM", "legacy_metric": "telecom_bandwidth_bytes"},
    )
    payload = record.to_dict()
    payload.update(overrides)
    return payload


class Tp101IngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "dev"
        os.environ.pop("TEGALCHAIN_REQUIRE_BEARER", None)
        os.environ.pop("MINT_WORKER_BEARER_TOKEN", None)
        os.environ["TEGALCHAIN_MINT_QUEUE_DB"] = str(Path(self.tmp.name) / "mint_queue.db")
        _queue_store.cache_clear()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        _queue_store.cache_clear()
        self.tmp.cleanup()
        os.environ.pop("TEGALCHAIN_MINT_QUEUE_DB", None)
        os.environ.pop("TEGALCHAIN_REQUIRE_BEARER", None)
        os.environ.pop("MINT_WORKER_BEARER_TOKEN", None)

    def test_submit_gtr_record_201(self) -> None:
        payload = _signed_gtr_v1_payload()
        response = self.client.post("/v1/telemetry/records", json=payload)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["gtr_id"], payload["gtr_id"])
        self.assertIsNone(body["ledger_ref"])
        self.assertEqual(body["status"], "pending")

    def test_get_gtr_record(self) -> None:
        payload = _signed_gtr_v1_payload()
        created = self.client.post("/v1/telemetry/records", json=payload).json()
        fetched = self.client.get(f"/v1/telemetry/records/{created['gtr_id']}")
        self.assertEqual(fetched.status_code, 200)
        body = fetched.json()
        self.assertEqual(body["gtr_id"], created["gtr_id"])
        self.assertEqual(len(body["attestations"]), 1)
        por = body.get("por_scores")
        self.assertIsNotNone(por)
        self.assertEqual(por.get("protocol_standard"), "TP-102")
        self.assertIn("eqs", por)
        self.assertIn("riv", por)
        self.assertIn("resonance_score", por)

    def test_submit_batch_202(self) -> None:
        records = [_signed_gtr_v1_payload(), _signed_gtr_v1_payload()]
        response = self.client.post("/v1/telemetry/batch", json={"records": records})
        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["accepted"], 2)
        batch = self.client.get(f"/v1/telemetry/batch/{body['batch_id']}")
        self.assertEqual(batch.status_code, 200)

    def test_bearer_required_when_configured(self) -> None:
        os.environ["MINT_WORKER_BEARER_TOKEN"] = "lab-secret-token"
        _queue_store.cache_clear()
        client = TestClient(app)
        payload = _signed_gtr_v1_payload()
        denied = client.post("/v1/telemetry/records", json=payload)
        self.assertEqual(denied.status_code, 401)
        ok = client.post(
            "/v1/telemetry/records",
            json=payload,
            headers={"Authorization": "Bearer lab-secret-token"},
        )
        self.assertEqual(ok.status_code, 201)

    def test_bearer_required_on_queue_routes(self) -> None:
        os.environ["MINT_WORKER_BEARER_TOKEN"] = "lab-secret-token"
        os.environ["TEGALCHAIN_REQUIRE_BEARER"] = "1"
        _queue_store.cache_clear()
        client = TestClient(app)
        denied = client.get("/v1/queue/stats")
        self.assertEqual(denied.status_code, 401)
        ok = client.get(
            "/v1/queue/stats",
            headers={"Authorization": "Bearer lab-secret-token"},
        )
        self.assertEqual(ok.status_code, 200)

    def test_get_carbon_account_requires_bearer(self) -> None:
        os.environ["MINT_WORKER_BEARER_TOKEN"] = "lab-secret-token"
        os.environ["TEGALCHAIN_REQUIRE_BEARER"] = "1"
        _queue_store.cache_clear()
        client = TestClient(app)
        denied = client.get("/v1/greenledger/carbon-accounts/carbon-node-1")
        self.assertEqual(denied.status_code, 401)

    def test_get_carbon_account(self) -> None:
        store = _queue_store()
        store.save_carbon_account(
            {
                "source_id": "carbon-node-1",
                "period_start": "2026-07-01T00:00:00Z",
                "period_end": "2026-07-31T23:59:59Z",
                "gross_emissions_kgco2e": 12.5,
                "offset_credits_kgco2e": 2.0,
                "net_emissions_kgco2e": 10.5,
                "data_completeness": 1.0,
                "last_updated": "2026-07-26T10:00:00Z",
                "schema_version": "1.0",
                "protocol_standard": "TP-103",
            }
        )
        response = self.client.get("/v1/greenledger/carbon-accounts/carbon-node-1")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["source_id"], "carbon-node-1")
        self.assertEqual(body["protocol_standard"], "TP-103")
        missing = self.client.get("/v1/greenledger/carbon-accounts/unknown-source")
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
