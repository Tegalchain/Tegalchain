"""FreeSWITCH CDR row parsed from the Zeegate lab CSV template."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CdrRow:
    uuid: str
    caller_id_number: str
    destination_number: str
    start_stamp: str
    end_stamp: str
    duration: int
    billsec: int
    hangup_cause: str
    read_bytes: int
    write_bytes: int

    @property
    def total_bytes(self) -> int:
        return self.read_bytes + self.write_bytes
