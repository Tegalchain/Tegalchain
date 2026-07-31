"""Bearer / OAuth 2.0 compatible auth for TP-101 HTTPS ingestion."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


def bearer_required() -> bool:
    if os.environ.get("TEGALCHAIN_REQUIRE_BEARER", "").lower() in {"1", "true", "yes"}:
        return True
    return bool(os.environ.get("MINT_WORKER_BEARER_TOKEN", "").strip())


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    """Enforce OAuth 2.0 Bearer token (or Tegalchain DID auth — future).

    Set MINT_WORKER_BEARER_TOKEN and optionally TEGALCHAIN_REQUIRE_BEARER=1.
    """
    if not bearer_required():
        return
    expected = os.environ.get("MINT_WORKER_BEARER_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Bearer auth required but MINT_WORKER_BEARER_TOKEN is not configured",
        )
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization[7:].strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid Bearer token")
