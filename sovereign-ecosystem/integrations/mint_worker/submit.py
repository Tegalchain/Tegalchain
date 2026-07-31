"""POST signed telemetry to the mint worker (stdlib HTTP client)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _resolve_bearer(bearer_token: str | None) -> str | None:
    if bearer_token:
        return bearer_token
    env = os.environ.get("MINT_WORKER_BEARER_TOKEN", "").strip()
    return env or None


def _request(
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    method: str = "POST",
    bearer_token: str | None = None,
) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Mint worker HTTP {exc.code}: {detail}") from exc


def submit_telemetry(
    mint_worker_url: str,
    payload: dict[str, Any],
    *,
    bearer_token: str | None = None,
    use_tp101_records: bool = False,
) -> dict[str, Any]:
    """Submit telemetry to mint worker; return parsed JSON response."""
    base = mint_worker_url.rstrip("/")
    path = "/v1/telemetry/records" if use_tp101_records else "/v1/telemetry"
    return _request(
        f"{base}{path}",
        payload,
        bearer_token=_resolve_bearer(bearer_token),
    )


def submit_gtr_batch(
    mint_worker_url: str,
    records: list[dict[str, Any]],
    *,
    bearer_token: str | None = None,
) -> dict[str, Any]:
    """POST /v1/telemetry/batch — up to 1,000 GTR records."""
    base = mint_worker_url.rstrip("/")
    return _request(
        f"{base}/v1/telemetry/batch",
        {"records": records},
        bearer_token=_resolve_bearer(bearer_token),
    )


def get_gtr_record(
    mint_worker_url: str,
    gtr_id: str,
    *,
    bearer_token: str | None = None,
) -> dict[str, Any]:
    """GET /v1/telemetry/records/{gtr_id}."""
    base = mint_worker_url.rstrip("/")
    return _request(
        f"{base}/v1/telemetry/records/{gtr_id}",
        None,
        method="GET",
        bearer_token=_resolve_bearer(bearer_token),
    )


def append_gtr_attestation(
    mint_worker_url: str,
    gtr_id: str,
    attestation: dict[str, Any],
    *,
    bearer_token: str | None = None,
) -> dict[str, Any]:
    """POST /v1/telemetry/records/{gtr_id}/attestations — TP-108 append."""
    base = mint_worker_url.rstrip("/")
    return _request(
        f"{base}/v1/telemetry/records/{gtr_id}/attestations",
        attestation,
        bearer_token=_resolve_bearer(bearer_token),
    )
