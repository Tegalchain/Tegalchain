"""Tests for Tegalchain GTR source identity registry."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.source_registry import (  # noqa: E402
    SourceRegistry,
    SourceRegistryError,
    assert_source_registered,
)


class SourceRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.registry_path = Path(self.tmp.name) / "sources.json"
        self.registry_path.write_text(
            json.dumps(
                {
                    "sources": [
                        {"source_id": "active-node", "status": "ACTIVE"},
                        {"source_id": "suspended-node", "status": "SUSPENDED"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        os.environ["TEGALID_SOURCE_REGISTRY_FILE"] = str(self.registry_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("TEGALID_SOURCE_REGISTRY_FILE", None)

    def test_active_source_registered(self) -> None:
        registry = SourceRegistry(self.registry_path)
        self.assertTrue(registry.is_registered("active-node"))
        source = assert_source_registered("active-node")
        self.assertEqual(source.source_id, "active-node")

    def test_unknown_source_rejected(self) -> None:
        with self.assertRaises(SourceRegistryError):
            assert_source_registered("missing-node")

    def test_suspended_source_rejected(self) -> None:
        with self.assertRaises(SourceRegistryError):
            assert_source_registered("suspended-node")


if __name__ == "__main__":
    unittest.main()
