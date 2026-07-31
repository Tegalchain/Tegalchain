"""Tests for TP-103 storage tiers and integrity verification."""

from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from green_ledger_spec.integrity import (  # noqa: E402
    IntegritySchedule,
    run_integrity_checks,
)
from green_ledger_spec.storage import (  # noqa: E402
    ReplicationPolicy,
    StorageTier,
    classify_storage_tier,
)


class StorageTierTests(unittest.TestCase):
    def test_hot_vs_cold_classification(self) -> None:
        now = datetime(2026, 7, 1, tzinfo=UTC)
        hot_ts = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        cold_ts = (now - timedelta(days=800)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(
            classify_storage_tier(hot_ts, now=now),
            StorageTier.HOT,
        )
        self.assertEqual(
            classify_storage_tier(cold_ts, now=now),
            StorageTier.COLD,
        )

    def test_replication_policy(self) -> None:
        policy = ReplicationPolicy(min_sites=2)
        self.assertTrue(policy.satisfies_requirement(2))
        self.assertFalse(policy.satisfies_requirement(1))


class IntegrityTests(unittest.TestCase):
    def test_detects_bad_content_hash(self) -> None:
        gles = [
            {
                "gle_id": "bad-gle",
                "gtr_id": "550e8400-e29b-41d4-a716-446655440099",
                "ledger_ref": "LABMOCK-1",
                "content_hash": "not-a-valid-hash",
                "archive_timestamp": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        ]
        violations = run_integrity_checks(gles, schedule=IntegritySchedule.DAILY)
        self.assertGreaterEqual(len(violations), 1)
        self.assertEqual(violations[0].kind.value, "CONTENT_HASH_MISMATCH")


if __name__ == "__main__":
    unittest.main()
