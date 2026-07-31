"""Tests for CDR CSV parsing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ZEEGATE_CLOUD = Path(__file__).resolve().parents[1]
if str(ZEEGATE_CLOUD) not in sys.path:
    sys.path.insert(0, str(ZEEGATE_CLOUD))

from cdr_adapter.parse import call_id_hash, fs_stamp_to_iso8601, parse_cdr_line  # noqa: E402


class CdrParseTests(unittest.TestCase):
    def test_parse_lab_row(self) -> None:
        line = (
            '"550e8400-e29b-41d4-a716-446655440001","edge001","1000",'
            '"2026-07-26 12:00:00","2026-07-26 12:01:30","90","85",'
            '"NORMAL_CLEARING","4096","8192"'
        )
        row = parse_cdr_line(line)
        self.assertEqual(row.caller_id_number, "edge001")
        self.assertEqual(row.total_bytes, 12288)
        self.assertEqual(row.duration, 90)

    def test_fs_stamp_to_iso8601(self) -> None:
        self.assertEqual(
            fs_stamp_to_iso8601("2026-07-26 12:01:30"),
            "2026-07-26T12:01:30Z",
        )

    def test_call_id_hash_is_stable(self) -> None:
        value = call_id_hash("550e8400-e29b-41d4-a716-446655440001")
        self.assertEqual(len(value), 64)
        self.assertEqual(value, call_id_hash("550e8400-e29b-41d4-a716-446655440001"))

    def test_parse_loopback_row_empty_byte_counters(self) -> None:
        line = (
            '"2c8efac9-d858-47ed-a7e7-edcb23875971","edge001","1000",'
            '"2026-07-28 09:04:10","2026-07-28 09:04:12","2","0",'
            '"NORMAL_CLEARING","",""'
        )
        row = parse_cdr_line(line)
        self.assertEqual(row.read_bytes, 0)
        self.assertEqual(row.write_bytes, 0)
        self.assertEqual(row.total_bytes, 0)


if __name__ == "__main__":
    unittest.main()
