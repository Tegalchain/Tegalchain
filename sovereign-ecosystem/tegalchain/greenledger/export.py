"""TP-103 cold-tier export adapter — JSONL snapshot for object storage handoff."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from green_ledger_spec.storage import StorageTier, classify_storage_tier

from tegalchain.queue.store import MintQueueStore


@dataclass(frozen=True, slots=True)
class ColdTierExportResult:
    output_path: str
    exported_count: int
    hot_skipped: int
    total_entries: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_path": self.output_path,
            "exported_count": self.exported_count,
            "hot_skipped": self.hot_skipped,
            "total_entries": self.total_entries,
        }


def export_cold_tier_entries(
    store: MintQueueStore,
    output_dir: Path,
    *,
    now: datetime | None = None,
) -> ColdTierExportResult:
    """Write cold-tier GLE rows to a timestamped JSONL file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    gles = store.list_all_greenledger_entries()
    cold: list[dict[str, Any]] = []
    hot_skipped = 0
    for gle in gles:
        tier = classify_storage_tier(str(gle.get("archive_timestamp", "")), now=now)
        if tier == StorageTier.COLD:
            cold.append(gle)
        else:
            hot_skipped += 1

    stamp = (now or datetime.now(tz=UTC)).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"gle_cold_export_{stamp}.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for gle in cold:
            handle.write(json.dumps(gle, separators=(",", ":"), sort_keys=True))
            handle.write("\n")

    return ColdTierExportResult(
        output_path=str(output_path),
        exported_count=len(cold),
        hot_skipped=hot_skipped,
        total_entries=len(gles),
    )
