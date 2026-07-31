"""Tests for submitter watch logging (Phase 7 soak)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter.backends import SubmitterBackend  # noqa: E402
from tegalchain.submitter.config import SubmitterConfig  # noqa: E402
from tegalchain.submitter.watch import watch_drain  # noqa: E402


class SubmitterWatchLogTests(unittest.TestCase):
    def test_watch_appends_jsonl_log_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MintQueueStore(Path(tmp) / "mint_queue.db")
            config = SubmitterConfig(
                db_path=store.db_path,
                outbox_dir=Path(tmp) / "outbox",
                backend=SubmitterBackend.MOCK,
                api_url="http://localhost:12391",
                privkey=None,
                qortal_service="99",
                qortal_data_type="JSON",
                tx_pl_path=Path("/nonexistent/tx.pl"),
                cosmos_rest_url="http://localhost:1317",
                cosmos_anchor_path="/tegalchain/gretelemetry/v1/anchor",
                cosmos_bearer_token=None,
            )
            log_file = Path(tmp) / "soak_watch.log"
            with patch("tegalchain.submitter.watch.time.sleep"):
                watch_drain(
                    store,
                    config,
                    limit=5,
                    interval_seconds=1,
                    max_cycles=2,
                    emit_json=True,
                    log_file=log_file,
                )
            self.assertTrue(log_file.is_file())
            lines = [line for line in log_file.read_text(encoding="utf-8").splitlines() if line]
            self.assertEqual(len(lines), 2)
            for index, line in enumerate(lines, start=1):
                payload = json.loads(line)
                self.assertEqual(payload["cycle"], index)
                self.assertIn("logged_at", payload)
                self.assertIn("sla", payload)
                self.assertEqual(payload["sla"]["violation_count"], 0)


if __name__ == "__main__":
    unittest.main()
