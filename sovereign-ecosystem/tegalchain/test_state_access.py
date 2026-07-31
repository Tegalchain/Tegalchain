"""Tests for contract state access patterns."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.contract_interface import StateView  # noqa: E402
from tegalchain.state import StateDatabaseBackend  # noqa: E402
from tegalchain.state_access import RichQueryNotSupportedError  # noqa: E402


class StateAccessPatternTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = StateView(backend=StateDatabaseBackend.LEVELDB)

    def test_get_put_delete(self) -> None:
        self.state.put("asset:a1", {"id": "a1", "owner": "o1"})
        self.assertEqual(self.state.get("asset:a1")["owner"], "o1")
        self.state.delete("asset:a1")
        self.assertIsNone(self.state.get("asset:a1"))

    def test_get_range(self) -> None:
        self.state.put("asset:a1", 1)
        self.state.put("asset:a2", 2)
        self.state.put("asset:b1", 3)
        rows = self.state.get_range("asset:a", "asset:b")
        self.assertEqual(rows, [("asset:a1", 1), ("asset:a2", 2)])

    def test_get_query_requires_couchdb(self) -> None:
        with self.assertRaises(RichQueryNotSupportedError):
            self.state.get_query({"selector": {"owner": "o1"}})

    def test_get_query_couchdb(self) -> None:
        couch = StateView(backend=StateDatabaseBackend.COUCHDB)
        couch.put("asset:a1", {"id": "a1", "owner": "o1"})
        couch.put("asset:a2", {"id": "a2", "owner": "o2"})
        matches = couch.get_query({"selector": {"owner": "o1"}})
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], "a1")

    def test_get_history(self) -> None:
        self.state.put("asset:a1", {"owner": "o1"})
        self.state.put("asset:a1", {"owner": "o2"})
        self.state.delete("asset:a1")
        history = self.state.get_history("asset:a1")
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].value, {"owner": "o1"})
        self.assertEqual(history[2].value, None)


if __name__ == "__main__":
    unittest.main()
