"""Tests for tegalid mint gate and gretelemetry v1.1 integration."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import Metrics, SovereignNodeTelemetry, SystemType  # noqa: E402
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_telemetry  # noqa: E402
from tegalchain.mint import mint_from_telemetry  # noqa: E402
from tegalchain.tegalid_gate import (  # noqa: E402
    BindingStore,
    TegalidGateError,
    assert_mint_eligible,
    is_tegalid_did,
    resolve_ingest_signing_secret,
)


EXAMPLE_BINDINGS = ROOT / "tegalchain" / "data" / "tegalid_bindings.example.json"
LAB_HMAC = b"sovereign-lab-hmac-secret01"


def _signed_tegalid_payload(**overrides: object) -> dict:
    unsigned = SovereignNodeTelemetry(
        node_id="did:tegal:LABEDGE001",
        project_id="zeegate-telecom",
        binding_id="edge-sim-01",
        timestamp=int(time.time()),
        system_type=SystemType.ZEEGATE_TELECOM,
        metrics=Metrics(telecom_bandwidth_bytes=8192),
        signature="",
    )
    data = unsigned.to_dict()
    for key, value in overrides.items():
        data[key] = value
    data.pop("signature", None)
    canonical = json.dumps(data, separators=(",", ":"), sort_keys=True)
    data["signature"] = sign_payload(canonical, LAB_HMAC)
    return data


class TegalidGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        shutil.copy(EXAMPLE_BINDINGS, Path(self.tmp.name) / "bindings.json")
        self.store = BindingStore(Path(self.tmp.name) / "bindings.json")
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "tegalid"
        os.environ["TEGALID_BINDINGS_FILE"] = str(Path(self.tmp.name) / "bindings.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("TEGALCHAIN_IDENTITY_MODE", None)
        os.environ.pop("TEGALID_BINDINGS_FILE", None)

    def test_is_tegalid_did(self) -> None:
        self.assertTrue(is_tegalid_did("did:tegal:LABEDGE001"))
        self.assertFalse(is_tegalid_did("test-node-001"))

    def test_assert_mint_eligible_success(self) -> None:
        payload = _signed_tegalid_payload()
        binding = assert_mint_eligible(payload, self.store)
        self.assertIsNotNone(binding)
        assert binding is not None
        self.assertEqual(binding.tegal_address, "TEGAL-LABEDGE001GREENLEDGER")

    def test_rejects_unknown_did(self) -> None:
        payload = _signed_tegalid_payload(node_id="did:tegal:UNKNOWN999")
        with self.assertRaises(TegalidGateError):
            assert_mint_eligible(payload, self.store)

    def test_rejects_project_mismatch(self) -> None:
        payload = _signed_tegalid_payload(project_id="wrong-project")
        with self.assertRaises(TegalidGateError):
            assert_mint_eligible(payload, self.store)

    def test_rejects_unregistered_project_binding(self) -> None:
        bad_path = Path(self.tmp.name) / "bad_bindings.json"
        bad_path.write_text(
            json.dumps(
                {
                    "bindings": [
                        {
                            "did": "did:tegal:BADPROJECT1",
                            "project_id": "not-a-registered-project",
                            "system_type": "ZEEGATE_TELECOM",
                            "binding_id": "x1",
                            "kyc_level": "VERIFIED",
                            "attestation_score": 100,
                            "status": "ACTIVE",
                            "mint_eligible": True,
                            "tegal_address": "TEGAL-BAD",
                            "telemetry_key_id": "k1",
                            "telemetry_hmac_secret_hex": LAB_HMAC.hex(),
                            "sip_user": "",
                            "sip_domain": "",
                            "sip_credential_commitment": "",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        store = BindingStore(bad_path)
        payload = _signed_tegalid_payload(
            node_id="did:tegal:BADPROJECT1",
            project_id="not-a-registered-project",
        )
        with self.assertRaises(TegalidGateError):
            assert_mint_eligible(payload, store)

    def test_mint_includes_tegalid_fields(self) -> None:
        payload = _signed_tegalid_payload()
        binding = assert_mint_eligible(payload, self.store)
        result = mint_from_telemetry(payload, binding)
        self.assertEqual(result.block_candidate["tegalid_did"], "did:tegal:LABEDGE001")
        self.assertEqual(result.block_candidate["project_id"], "zeegate-telecom")
        self.assertEqual(result.block_candidate["auditrail_record_type"], "GREETELEMETRY")


class IngestSigningSecretTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "dev"
        os.environ["TEGALID_BINDINGS_FILE"] = str(EXAMPLE_BINDINGS)

    def tearDown(self) -> None:
        os.environ.pop("TEGALCHAIN_IDENTITY_MODE", None)
        os.environ.pop("TEGALID_BINDINGS_FILE", None)

    def test_dev_mode_resolves_binding_secret_for_tegalid_gtr(self) -> None:
        from greentelemetry_protocol_spec.models import MeasurementType, SourceType  # noqa: PLC0415
        from greentelemetry_protocol_spec.signing import DEFAULT_HMAC_SECRET  # noqa: PLC0415
        from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: PLC0415

        record = build_signed_tp101_gtr(
            source_id="did:tegal:LABEDGE001",
            source_type=SourceType.API,
            measurement_type=MeasurementType.CUSTOM,
            value=1.0,
            unit="bytes",
            metadata={"system_type": "ZEEGATE_TELECOM"},
            project_id="zeegate-telecom",
            binding_id="edge-sim-01",
            signing_secret=LAB_HMAC,
        )
        secret = resolve_ingest_signing_secret(record.to_dict(), "gtr_v1", None)
        self.assertEqual(secret, LAB_HMAC)
        self.assertNotEqual(secret, DEFAULT_HMAC_SECRET)


class GretelemetryV11SchemaTests(unittest.TestCase):
    def test_v1_payload_still_valid(self) -> None:
        payload = {
            "node_id": "test-node-001",
            "timestamp": 1,
            "system_type": "ZEEGATE_TELECOM",
            "metrics": {"telecom_bandwidth_bytes": 100},
            "signature": "hmac-sha256:" + "a" * 64,
        }
        telemetry = validate_telemetry(payload)
        self.assertIsNone(telemetry.project_id)

    def test_v11_optional_fields(self) -> None:
        payload = {
            "node_id": "did:tegal:LABEDGE001",
            "project_id": "zeegate-telecom",
            "binding_id": "edge-sim-01",
            "timestamp": 1,
            "system_type": "ZEEGATE_TELECOM",
            "metrics": {"telecom_bandwidth_bytes": 100},
            "signature": "hmac-sha256:" + "b" * 64,
        }
        telemetry = validate_telemetry(payload)
        self.assertEqual(telemetry.project_id, "zeegate-telecom")
        self.assertEqual(telemetry.binding_id, "edge-sim-01")


class ProjectRegistryTests(unittest.TestCase):
    def test_active_projects_cover_both_verticals(self) -> None:
        from tegalchain.project_registry import resolve_project_registry  # noqa: PLC0415

        registry = resolve_project_registry()
        active = {p.project_id for p in registry.active_projects()}
        self.assertIn("zeegate-telecom", active)
        self.assertIn("bytenergy-utility", active)

    def test_planned_project_not_mint_ready(self) -> None:
        from tegalchain.project_registry import resolve_project_registry  # noqa: PLC0415

        project = resolve_project_registry().get("example-env-sensor")
        assert project is not None
        self.assertFalse(project.is_mint_ready)


if __name__ == "__main__":
    unittest.main()
