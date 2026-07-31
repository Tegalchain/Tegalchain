"""Tests for TP-108 attestation append pipeline."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_attestation_spec.attestation import (  # noqa: E402
    build_third_party_attestation,
    tp108_metadata_from_corroboration,
)
from ai_attestation_spec.keys import DEFAULT_MODEL_PROFILE  # noqa: E402
from ai_attestation_spec.zeegate_corroboration import corroborate_from_fixture  # noqa: E402
from greentelemetry_protocol_spec.models import Metrics, SovereignNodeTelemetry, SystemType  # noqa: E402
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from integrations.mint_worker.ingest import ingest_payload  # noqa: E402
from integrations.mint_worker.tp108_append import Tp108AppendError, append_attestation  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402

LAB_BINDINGS = ROOT / "tegalchain" / "data" / "tegalid_bindings.example.json"
LAB_HMAC = bytes.fromhex("736f7665726569676e2d6c61622d686d61632d7365637265743031")
FIXTURE = ROOT / "zeegate-cloud" / "cdr_adapter" / "fixtures" / "sample_cdr.csv"


def _signed_zeegate_payload() -> dict:
    unsigned = SovereignNodeTelemetry(
        node_id="did:tegal:LABEDGE001",
        timestamp=int(time.time()),
        system_type=SystemType.ZEEGATE_TELECOM,
        metrics=Metrics(telecom_bandwidth_bytes=1048576),
        project_id="zeegate-telecom",
        binding_id="edge-sim-01",
        signature="",
    )
    canonical = unsigned_canonical_json(unsigned.to_dict())
    return SovereignNodeTelemetry(
        node_id=unsigned.node_id,
        timestamp=unsigned.timestamp,
        system_type=unsigned.system_type,
        metrics=unsigned.metrics,
        project_id=unsigned.project_id,
        binding_id=unsigned.binding_id,
        signature=sign_payload(canonical, LAB_HMAC),
    ).to_dict()


class Tp108AppendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "mint_queue.db"
        os.environ["TEGALCHAIN_MINT_QUEUE_DB"] = str(self.db_path)
        os.environ["TEGALID_BINDINGS_FILE"] = str(LAB_BINDINGS)
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "tegalid"
        os.environ["MINT_WORKER_VALIDATE_TP108"] = "1"
        self.store = MintQueueStore(self.db_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for key in (
            "TEGALCHAIN_MINT_QUEUE_DB",
            "TEGALID_BINDINGS_FILE",
            "TEGALCHAIN_IDENTITY_MODE",
            "MINT_WORKER_VALIDATE_TP108",
        ):
            os.environ.pop(key, None)

    def test_append_third_party_attestation(self) -> None:
        ingested = ingest_payload(self.store, _signed_zeegate_payload())
        gtr_id = ingested.gtr_id
        tp101 = ingested.block_candidate["tp101_record"]
        result = corroborate_from_fixture(tp101, FIXTURE)
        tp108 = tp108_metadata_from_corroboration(result, model_profile=DEFAULT_MODEL_PROFILE)
        attestation = build_third_party_attestation(tp101, tp108=tp108, confidence=0.9)

        updated = append_attestation(self.store, gtr_id, attestation)
        tp101_updated = updated.block_candidate["tp101_record"]
        self.assertEqual(len(tp101_updated["attestations"]), 2)
        third_party = [
            att for att in tp101_updated["attestations"] if att["attester_type"] == "THIRD_PARTY"
        ]
        self.assertEqual(len(third_party), 1)
        self.assertEqual(third_party[0]["metadata"]["tp108"]["verdict"], "PASS")

    def test_rejects_duplicate_claim(self) -> None:
        ingested = ingest_payload(self.store, _signed_zeegate_payload())
        tp101 = ingested.block_candidate["tp101_record"]
        result = corroborate_from_fixture(tp101, FIXTURE)
        tp108 = tp108_metadata_from_corroboration(result, model_profile=DEFAULT_MODEL_PROFILE)
        attestation = build_third_party_attestation(tp101, tp108=tp108, confidence=0.9)
        append_attestation(self.store, ingested.gtr_id, attestation)
        with self.assertRaises(Tp108AppendError):
            append_attestation(self.store, ingested.gtr_id, attestation)


if __name__ == "__main__":
    unittest.main()
