"""Parse FreeSWITCH zeegate CDR CSV rows."""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import UTC, datetime

from .models import CdrRow


class CdrParseError(ValueError):
    """Malformed CDR CSV row."""


def _parse_int_field(value: str, field_name: str) -> int:
    """Parse numeric CDR fields; FreeSWITCH may emit empty byte counters on loopback."""
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError as exc:
        raise CdrParseError(f"invalid {field_name}: {value!r}") from exc


def fs_stamp_to_iso8601(stamp: str) -> str:
    """Convert FreeSWITCH stamp to TP-101 UTC ISO 8601."""
    normalized = stamp.strip().replace("T", " ")
    if normalized.endswith("Z"):
        normalized = normalized[:-1]
    parsed = datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
    return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")


def call_id_hash(uuid: str) -> str:
    """Public call identifier hash — raw SIP/UUID not sent to the oracle."""
    return hashlib.sha256(uuid.encode("utf-8")).hexdigest()


def parse_cdr_line(line: str) -> CdrRow:
    """Parse one CSV line from the zeegate CDR template."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        raise CdrParseError("empty or comment line")
    reader = csv.reader(io.StringIO(stripped))
    row = next(reader)
    if len(row) != 10:
        raise CdrParseError(f"expected 10 CSV fields, got {len(row)}")
    try:
        return CdrRow(
            uuid=str(row[0]).strip(),
            caller_id_number=str(row[1]).strip(),
            destination_number=str(row[2]).strip(),
            start_stamp=str(row[3]).strip(),
            end_stamp=str(row[4]).strip(),
            duration=_parse_int_field(row[5], "duration"),
            billsec=_parse_int_field(row[6], "billsec"),
            hangup_cause=str(row[7]).strip(),
            read_bytes=_parse_int_field(row[8], "read_bytes"),
            write_bytes=_parse_int_field(row[9], "write_bytes"),
        )
    except CdrParseError:
        raise
    except (TypeError, ValueError) as exc:
        raise CdrParseError(f"invalid CDR field types: {exc}") from exc


def parse_cdr_file(content: str) -> list[CdrRow]:
    rows: list[CdrRow] = []
    for line in content.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        rows.append(parse_cdr_line(line))
    return rows
