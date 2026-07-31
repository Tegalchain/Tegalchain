"""Tests for ZK evidence on final Greenledger gretelemetry."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import (  # noqa: E402
    EvidenceKind,
    Metrics,
    SovereignNodeTelemetry,
    SystemType,
    ZkEvidence,
)
from greentelemetry_protocol_spec.signing import sign_payload  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_telemetry  # noqa: E402
from tegalchain.mint import mint_from_telemetry  # noqa: E402
from tegalchain.zk_evidence import (  # noqa: E402
    ZkEvidenceError,
    public_inputs_hash,
    verify_zk_evidence,
)


def _payload_with_zk(*, include_zk: bool = True) -> dict:
    base = SovereignNodeTelemetry(
        node_id="test-zk-node",
        timestamp=1700000000,
        system_type=SystemType.ZEEGATE_TELECOM,
        metrics=Metrics(telecom_bandwidth_bytes=1024),
        signature="",
    )
    data = base.to_dict()
    if include_zk:
        pi_hash = public_inputs_hash(data)
        data["zk_evidence"] = ZkEvidence(
            scheme="placeholder-dev",
            circuit_id="gretelemetry-v1",
            evidence_kind=EvidenceKind.GREETELEMETRY,
            public_inputs_hash=pi_hash,
            commitment="abc123",
            proof="00",
        ).to_dict()
    unsigned = {k: v for k, v in data.items() if k != "signature"}
    data["signature"] = sign_payload(
        json.dumps(unsigned, separators=(",", ":"), sort_keys=True)
    )
    return data


class ZkEvidenceTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("TEGALCHAIN_ZK_MODE", None)

    def test_schema_accepts_zk_evidence(self) -> None:
        payload = _payload_with_zk()
        telemetry = validate_telemetry(payload)
        assert telemetry.zk_evidence is not None
        self.assertEqual(telemetry.zk_evidence.evidence_kind, EvidenceKind.GREETELEMETRY)

    def test_verify_dev_mode_with_zk(self) -> None:
        os.environ["TEGALCHAIN_ZK_MODE"] = "dev"
        payload = _payload_with_zk()
        telemetry = validate_telemetry(payload)
        zk = verify_zk_evidence(telemetry)
        assert zk is not None
        self.assertEqual(zk.scheme, "placeholder-dev")

    def test_required_mode_rejects_missing_zk(self) -> None:
        os.environ["TEGALCHAIN_ZK_MODE"] = "required"
        payload = _payload_with_zk(include_zk=False)
        telemetry = validate_telemetry(payload)
        with self.assertRaises(ZkEvidenceError):
            verify_zk_evidence(telemetry)

    def test_mint_block_includes_zk(self) -> None:
        payload = _payload_with_zk()
        result = mint_from_telemetry(payload)
        self.assertIn("zk_evidence", result.block_candidate)
        self.assertEqual(
            result.block_candidate["zk_evidence"]["evidence_kind"],
            "GREETELEMETRY",
        )


if __name__ == "__main__":
    unittest.main()
