"""Watch FreeSWITCH CDR CSV directory and publish adapter-normalized GTRs."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapter import CdrAdapter
from .parse import CdrParseError, parse_cdr_file, parse_cdr_line
from .state import CdrWatcherState


@dataclass(frozen=True, slots=True)
class CdrWatchResult:
    scanned_files: int
    processed_rows: int
    skipped_rows: int
    errors: tuple[str, ...]
    responses: tuple[dict[str, Any], ...]


def _iter_cdr_files(cdr_dir: Path) -> list[Path]:
    if not cdr_dir.is_dir():
        return []
    return sorted(path for path in cdr_dir.glob("*.csv") if path.is_file())


def process_cdr_directory(
    adapter: CdrAdapter,
    cdr_dir: Path,
    state: CdrWatcherState,
) -> CdrWatchResult:
    scanned = processed = skipped = 0
    errors: list[str] = []
    responses: list[dict[str, Any]] = []

    for path in _iter_cdr_files(cdr_dir):
        scanned += 1
        content = path.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            try:
                row = parse_cdr_line(line)
            except CdrParseError as exc:
                errors.append(f"{path.name}: {exc}")
                continue
            if state.is_processed(row.uuid):
                skipped += 1
                continue
            try:
                response = adapter.publish_row(row)
            except Exception as exc:  # noqa: BLE001 — per-row failure
                errors.append(f"{path.name} uuid={row.uuid}: {exc}")
                continue
            gtr_id = response.get("gtr_id")
            state.mark_processed(row.uuid, gtr_id=str(gtr_id) if gtr_id else None)
            processed += 1
            responses.append(response)

    return CdrWatchResult(
        scanned_files=scanned,
        processed_rows=processed,
        skipped_rows=skipped,
        errors=tuple(errors),
        responses=tuple(responses),
    )


def watch_cdr_directory(
    adapter: CdrAdapter,
    cdr_dir: Path,
    state: CdrWatcherState,
    *,
    interval_seconds: int = 15,
    max_cycles: int | None = None,
) -> list[CdrWatchResult]:
    cycles: list[CdrWatchResult] = []
    iteration = 0
    while max_cycles is None or iteration < max_cycles:
        cycles.append(process_cdr_directory(adapter, cdr_dir, state))
        iteration += 1
        if max_cycles is not None and iteration >= max_cycles:
            break
        time.sleep(interval_seconds)
    return cycles
