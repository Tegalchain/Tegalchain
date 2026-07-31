"""Tests for CDR → GTR adapter normalization."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ZEEGATE_CLOUD = Path(__file__).resolve().parents[1]
for path in (str(REPO_ROOT), str(ZEEGATE_CLOUD)):
    if path not in sys.path:
        sys.path.insert(0, path)

from greentelemetry_protocol_spec.models import MeasurementType  # noqa: E402
from greentelemetry_protocol_spec.signing import verify_gtr_attestations  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_gretelemetry  # noqa: E402

from cdr_adapter.adapter import CdrAdapter, CdrAdapterConfig  # noqa: E402
from cdr_adapter.parse import parse_cdr_line  # noqa: E402
from cdr_adapter.state import CdrWatcherState  # noqa: E402
from cdr_adapter.watcher import process_cdr_directory  # noqa: E402


SAMPLE_LINE = (
    '"550e8400-e29b-41d4-a716-446655440001","edge001","1000",'
    '"2026-07-26 12:00:00","2026-07-26 12:01:30","90","85",'
    '"NORMAL_CLEARING","4096","8192"'
)


class CdrAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bindings = REPO_ROOT / "tegalchain" / "data" / "tegalid_bindings.example.json"
        self.adapter = CdrAdapter(
            CdrAdapterConfig(bindings_file=self.bindings, fallback_source_id="edge001")
        )
        self.row = parse_cdr_line(SAMPLE_LINE)

    def test_maps_sip_user_to_tegalid_did(self) -> None:
        source_id, project_id, binding_id, _secret = self.adapter.source_for_row(self.row)
        self.assertEqual(source_id, "did:tegal:LABEDGE001")
        self.assertEqual(project_id, "zeegate-telecom")
        self.assertEqual(binding_id, "edge-sim-01")

    def test_build_gtr_cdr_metadata(self) -> None:
        record = self.adapter.build_gtr(self.row)
        self.assertEqual(record.measurement_type, MeasurementType.CUSTOM)
        self.assertEqual(record.value, 12288.0)
        self.assertEqual(record.metadata["evidence_kind"], "CDR")
        self.assertEqual(record.metadata["adapter"], "zeegate_cdr")
        self.assertNotIn(self.row.uuid, record.metadata["call_id_hash"])

    def test_gtr_validates_with_binding_secret(self) -> None:
        record = self.adapter.build_gtr(self.row)
        _source_id, _project_id, _binding_id, secret = self.adapter.source_for_row(self.row)
        payload = record.to_dict()
        verify_gtr_attestations(payload, secret)
        validated = validate_gretelemetry(payload, signing_secret=secret)
        self.assertEqual(validated.tp101.source_id, "did:tegal:LABEDGE001")

    def test_watcher_dedupes_by_uuid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cdr_dir = Path(tmp) / "cdr"
            cdr_dir.mkdir()
            (cdr_dir / "Master.csv").write_text(SAMPLE_LINE + "\n", encoding="utf-8")
            state = CdrWatcherState(Path(tmp) / "state.db")
            first = process_cdr_directory(self.adapter, cdr_dir, state)
            second = process_cdr_directory(self.adapter, cdr_dir, state)
            self.assertEqual(first.processed_rows, 1)
            self.assertEqual(second.processed_rows, 0)
            self.assertEqual(second.skipped_rows, 1)


if __name__ == "__main__":
    unittest.main()
