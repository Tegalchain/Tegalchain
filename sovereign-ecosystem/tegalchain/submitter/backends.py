"""Pluggable mint queue submit backends (outbox, lab mock, Cosmos REST, legacy Qortal)."""

from __future__ import annotations

import os
from enum import Enum


class SubmitterBackend(str, Enum):
    """Where drained TELEMETRY_MINT proposals are ordered."""

    OUTBOX = "outbox"
    MOCK = "mock"
    COSMOS = "cosmos"
    QORTAL = "qortal"


def resolve_submitter_backend(*, privkey: str | None = None) -> SubmitterBackend:
    """Resolve backend from env. Default: mock in lab, qortal if privkey only, else outbox."""
    raw = os.environ.get("TEGALCHAIN_SUBMITTER_BACKEND", "").strip().lower()
    if raw:
        return SubmitterBackend(raw)

    if os.environ.get("TEGALCHAIN_LAB_MOCK_SUBMIT", "").lower() in {"1", "true", "yes"}:
        return SubmitterBackend.MOCK

    if os.environ.get("TEGALCHAIN_COSMOS_REST_URL", "").strip():
        return SubmitterBackend.COSMOS

    if privkey:
        return SubmitterBackend.QORTAL

    return SubmitterBackend.OUTBOX


def backend_submits_to_chain(backend: SubmitterBackend) -> bool:
    return backend is not SubmitterBackend.OUTBOX
