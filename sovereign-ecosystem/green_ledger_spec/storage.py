"""TP-103 layered storage — hot/cold tier classification and replication policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum

HOT_TIER_MONTHS = 24
COLD_RETRIEVAL_SLA_HOURS = 48
HOT_QUERY_P95_MS = 500
MIN_REPLICATION_SITES = 2


class StorageTier(str, Enum):
    HOT = "HOT"
    COLD = "COLD"


@dataclass(frozen=True, slots=True)
class ReplicationPolicy:
    min_sites: int = MIN_REPLICATION_SITES
    federation_enabled: bool = False

    def satisfies_requirement(self, site_count: int) -> bool:
        return site_count >= self.min_sites


def classify_storage_tier(
    archive_timestamp: str,
    *,
    now: datetime | None = None,
) -> StorageTier:
    """Hot tier: preceding 24 months; cold tier: older."""
    archived = datetime.fromisoformat(archive_timestamp.replace("Z", "+00:00"))
    current = now or datetime.now(tz=UTC)
    cutoff = current - timedelta(days=HOT_TIER_MONTHS * 30)
    if archived >= cutoff:
        return StorageTier.HOT
    return StorageTier.COLD


def is_hot_tier_query_eligible(archive_timestamp: str, *, now: datetime | None = None) -> bool:
    return classify_storage_tier(archive_timestamp, now=now) == StorageTier.HOT
