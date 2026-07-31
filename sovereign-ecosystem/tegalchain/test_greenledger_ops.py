"""Tests for Phase 7 GreenLedger ops — integrity runner and cold export."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from green_ledger_spec.integrity import IntegrityViolationKind, IntegritySchedule  # noqa: E402

from tegalchain.greenledger.export import export_cold_tier_entries  # noqa: E402
from tegalchain.greenledger.integrity_runner import run_and_persist_integrity_checks  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402


def _gle(
    *,
    gle_id: str = "gle-001",
    gtr_id: str = "550e8400-e29b-41d4-a716-446655440030",
    archive_timestamp: str = "2026-07-26T10:00:00Z",
    ledger_ref: str = "LABMOCK-001",
    content_hash: str = "a" * 64,
) -> dict[str, object]:
    return {
        "gle_id": gle_id,
        "gtr_id": gtr_id,
        "source_id": "ops-node-1",
        "measurement_type": "CUSTOM",
        "measurement_timestamp": "2026-07-26T10:00:00Z",
        "anchor_timestamp": "2026-07-26T10:00:05Z",
        "archive_timestamp": archive_timestamp,
        "ledger_ref": ledger_ref,
        "content_hash": content_hash,
        "value": 100.0,
        "unit": "bytes",
        "attestation_count": 1,
        "attestation_summary": [],
        "retention_class": "STANDARD",
        "protocol_standard": "TP-103",
        "schema_version": "1.0",
    }


class GreenLedgerOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MintQueueStore(Path(self.tmp.name) / "mint_queue.db")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_integrity_runner_persists_violations(self) -> None:
        now = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.store.save_greenledger_entry(
            _gle(content_hash="bad", archive_timestamp=now)  # type: ignore[arg-type]
        )
        result = run_and_persist_integrity_checks(
            self.store,
            schedule=IntegritySchedule.DAILY,
        )
        self.assertGreaterEqual(result.violation_count, 1)
        self.assertEqual(
            result.violations[0]["kind"],
            IntegrityViolationKind.CONTENT_HASH_MISMATCH.value,
        )

    def test_integrity_runner_clean_entries(self) -> None:
        now = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.store.save_greenledger_entry(
            _gle(archive_timestamp=now)  # type: ignore[arg-type]
        )
        result = run_and_persist_integrity_checks(
            self.store,
            schedule=IntegritySchedule.DAILY,
        )
        self.assertEqual(result.violation_count, 0)

    def test_export_cold_tier_skips_hot_rows(self) -> None:
        fixed_now = datetime(2026, 7, 28, 12, 0, 0, tzinfo=UTC)
        hot_ts = fixed_now.strftime("%Y-%m-%dT%H:%M:%SZ")
        cold_ts = (fixed_now - timedelta(days=800)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.store.save_greenledger_entry(
            _gle(archive_timestamp=hot_ts)  # type: ignore[arg-type]
        )
        self.store.save_greenledger_entry(
            _gle(
                gle_id="gle-cold",
                gtr_id="550e8400-e29b-41d4-a716-446655440031",
                archive_timestamp=cold_ts,
            )  # type: ignore[arg-type]
        )
        out_dir = Path(self.tmp.name) / "export"
        result = export_cold_tier_entries(self.store, out_dir, now=fixed_now)
        self.assertEqual(result.exported_count, 1)
        self.assertEqual(result.hot_skipped, 1)
        self.assertTrue(Path(result.output_path).is_file())


if __name__ == "__main__":
    unittest.main()
