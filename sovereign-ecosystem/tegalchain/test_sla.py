"""Tests for anchor SLA monitoring."""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.security import ANCHOR_SLA_SECONDS  # noqa: E402
from tegalchain.endorsement import ORACLE_PEER_ID, Endorsement, attach_endorsements  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter.sla import anchor_sla_violation, build_anchor_sla_report  # noqa: E402


def _candidate(*, accepted_at: str) -> dict[str, object]:
    base: dict[str, object] = {
        "type": "TELEMETRY_MINT",
        "signer": "addr",
        "timestamp": 1,
        "accepted_at": accepted_at,
        "on_chain_anchor": {
            "type": "GTR_ANCHOR",
            "gtr_id": "550e8400-e29b-41d4-a716-446655440099",
            "content_hash": "a" * 64,
            "attester_ids": ["n1"],
            "measurement_type": "ENERGY_KWH",
            "timestamp": "2026-07-26T12:00:00Z",
        },
    }
    return attach_endorsements(
        base,
        [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="sla-hash")],
    )


class AnchorSlaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = MintQueueStore(Path(self.tmp.name) / "mint_queue.db")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_no_violation_within_sla(self) -> None:
        accepted = datetime.now(tz=UTC).isoformat()
        self.store.enqueue(
            telemetry_hash="fresh-hash",
            gtr_id="550e8400-e29b-41d4-a716-446655440099",
            block_candidate=_candidate(accepted_at=accepted),
            state_update={"telemetry_hash": "fresh-hash"},
            identity={"node_id": "n1"},
        )
        record = self.store.fetch_by_gtr_id("550e8400-e29b-41d4-a716-446655440099")
        assert record is not None
        self.assertIsNone(anchor_sla_violation(record))

    def test_violation_after_sla_window(self) -> None:
        stale = (datetime.now(tz=UTC) - timedelta(seconds=ANCHOR_SLA_SECONDS + 5)).isoformat()
        self.store.enqueue(
            telemetry_hash="stale-hash",
            gtr_id="550e8400-e29b-41d4-a716-446655440098",
            block_candidate=_candidate(accepted_at=stale),
            state_update={"telemetry_hash": "stale-hash"},
            identity={"node_id": "n1"},
        )
        report = build_anchor_sla_report(self.store.fetch_unanchored())
        self.assertEqual(report.violation_count, 1)
        self.assertGreater(report.violations[0].age_seconds, ANCHOR_SLA_SECONDS)

    def test_submitted_rows_not_flagged(self) -> None:
        stale = (datetime.now(tz=UTC) - timedelta(seconds=ANCHOR_SLA_SECONDS + 5)).isoformat()
        queue_id = self.store.enqueue(
            telemetry_hash="done-hash",
            gtr_id="550e8400-e29b-41d4-a716-446655440097",
            block_candidate=_candidate(accepted_at=stale),
            state_update={"telemetry_hash": "done-hash"},
            identity={"node_id": "n1"},
        )
        self.store.mark_submitted(queue_id, "qortal-signature-abc")
        report = build_anchor_sla_report(self.store.fetch_unanchored())
        self.assertEqual(report.violation_count, 0)


if __name__ == "__main__":
    unittest.main()
