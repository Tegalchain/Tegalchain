"""TP-103 integrity verification schedules and violation reporting."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Iterable

from .storage import StorageTier, classify_storage_tier


class IntegritySchedule(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


class IntegrityViolationKind(str, Enum):
    CONTENT_HASH_MISMATCH = "CONTENT_HASH_MISMATCH"
    LEDGER_REF_MISMATCH = "LEDGER_REF_MISMATCH"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    COLD_TIER_UNREACHABLE = "COLD_TIER_UNREACHABLE"


@dataclass(frozen=True, slots=True)
class IntegrityViolation:
    gle_id: str
    kind: IntegrityViolationKind
    schedule: IntegritySchedule
    detail: str
    detected_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gle_id": self.gle_id,
            "kind": self.kind.value,
            "schedule": self.schedule.value,
            "detail": self.detail,
            "detected_at": self.detected_at,
        }


def _iso_now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify_gle_content_hash(gle: dict[str, Any]) -> IntegrityViolation | None:
    content_hash = str(gle.get("content_hash", ""))
    if len(content_hash) != 64 or not all(c in "0123456789abcdefABCDEF" for c in content_hash):
        return IntegrityViolation(
            gle_id=str(gle.get("gle_id", "unknown")),
            kind=IntegrityViolationKind.CONTENT_HASH_MISMATCH,
            schedule=IntegritySchedule.DAILY,
            detail="content_hash must be 64-char SHA-256 hex",
            detected_at=_iso_now(),
        )
    return None


def verify_ledger_ref_format(gle: dict[str, Any]) -> IntegrityViolation | None:
    ref = str(gle.get("ledger_ref", ""))
    if not ref:
        return IntegrityViolation(
            gle_id=str(gle.get("gle_id", "unknown")),
            kind=IntegrityViolationKind.LEDGER_REF_MISMATCH,
            schedule=IntegritySchedule.MONTHLY,
            detail="ledger_ref is required",
            detected_at=_iso_now(),
        )
    if ref.startswith("0x") and len(ref) != 66:
        return IntegrityViolation(
            gle_id=str(gle.get("gle_id", "unknown")),
            kind=IntegrityViolationKind.LEDGER_REF_MISMATCH,
            schedule=IntegritySchedule.MONTHLY,
            detail="0x-prefixed ledger_ref must be 66 characters",
            detected_at=_iso_now(),
        )
    return None


def entries_modified_within(
    gles: Iterable[dict[str, Any]],
    *,
    hours: int,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    current = now or datetime.now(tz=UTC)
    cutoff = current - timedelta(hours=hours)
    selected: list[dict[str, Any]] = []
    for gle in gles:
        ts = datetime.fromisoformat(
            str(gle.get("archive_timestamp", "")).replace("Z", "+00:00")
        )
        if ts >= cutoff:
            selected.append(gle)
    return selected


def sample_hot_tier_entries(
    gles: Iterable[dict[str, Any]],
    *,
    fraction: float = 0.05,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    hot = [
        gle
        for gle in gles
        if classify_storage_tier(str(gle.get("archive_timestamp", ""))) == StorageTier.HOT
    ]
    if not hot:
        return []
    rng = random.Random(seed)
    sample_size = max(1, int(len(hot) * fraction))
    return rng.sample(hot, min(sample_size, len(hot)))


def run_integrity_checks(
    gles: Iterable[dict[str, Any]],
    *,
    schedule: IntegritySchedule,
    on_chain_refs: dict[str, str] | None = None,
) -> list[IntegrityViolation]:
    """Run scheduled integrity verification; return violations (never silent fix)."""
    rows = list(gles)
    targets: list[dict[str, Any]]
    if schedule == IntegritySchedule.DAILY:
        targets = entries_modified_within(rows, hours=24)
    elif schedule == IntegritySchedule.WEEKLY:
        targets = sample_hot_tier_entries(rows, fraction=0.05)
    elif schedule == IntegritySchedule.MONTHLY:
        cutoff = datetime.now(tz=UTC) - timedelta(days=30)
        targets = [
            gle
            for gle in rows
            if datetime.fromisoformat(
                str(gle.get("archive_timestamp", "")).replace("Z", "+00:00")
            )
            >= cutoff
        ]
    else:
        targets = [
            gle
            for gle in rows
            if classify_storage_tier(str(gle.get("archive_timestamp", "")))
            == StorageTier.COLD
        ]

    violations: list[IntegrityViolation] = []
    for gle in targets:
        for check in (verify_gle_content_hash, verify_ledger_ref_format):
            result = check(gle)
            if result is not None:
                violations.append(
                    IntegrityViolation(
                        gle_id=result.gle_id,
                        kind=result.kind,
                        schedule=schedule,
                        detail=result.detail,
                        detected_at=result.detected_at,
                    )
                )
        if schedule == IntegritySchedule.MONTHLY and on_chain_refs is not None:
            gtr_id = str(gle.get("gtr_id", ""))
            expected = on_chain_refs.get(gtr_id)
            if expected is not None and str(gle.get("ledger_ref")) != expected:
                violations.append(
                    IntegrityViolation(
                        gle_id=str(gle.get("gle_id", "unknown")),
                        kind=IntegrityViolationKind.LEDGER_REF_MISMATCH,
                        schedule=schedule,
                        detail=f"ledger_ref mismatch for gtr_id {gtr_id}",
                        detected_at=_iso_now(),
                    )
                )
    return violations
