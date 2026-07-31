"""TP-103 retention policy helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from .models import RETENTION_YEARS, RetentionClass


def retention_expires_at(
    archive_timestamp: str,
    retention_class: RetentionClass,
) -> datetime | None:
    """Return expiry instant, or None for PERMANENT retention."""
    years = RETENTION_YEARS[retention_class.value]
    if years is None:
        return None
    archived = datetime.fromisoformat(archive_timestamp.replace("Z", "+00:00"))
    return archived + timedelta(days=365 * years)


def is_within_retention(
    archive_timestamp: str,
    retention_class: RetentionClass,
    *,
    now: datetime | None = None,
) -> bool:
    expiry = retention_expires_at(archive_timestamp, retention_class)
    if expiry is None:
        return True
    current = now or datetime.now(tz=UTC)
    return current <= expiry
