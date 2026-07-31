"""Cosmos SDK REST submitter for TELEMETRY_MINT anchors (TP-103 target path)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class CosmosSubmitError(RuntimeError):
    """Cosmos anchor submission failed."""


def submit_to_cosmos(
    block_candidate: dict[str, Any],
    *,
    rest_url: str,
    anchor_path: str,
    bearer_token: str | None = None,
    timeout_seconds: float = 30.0,
) -> str:
    """POST anchor payload to the Greenledger Cosmos lab/module endpoint.

    Expects JSON response containing one of: txhash, tx_hash, hash, submit_ref.
    Default path targets a future ``x/auditrail`` or gretelemetry anchor module.
    """
    base = rest_url.rstrip("/")
    path = anchor_path if anchor_path.startswith("/") else f"/{anchor_path}"
    url = f"{base}{path}"

    anchor = block_candidate.get("on_chain_anchor") or {}
    body = json.dumps(
        {
            "type": "TELEMETRY_MINT",
            "block_candidate": block_candidate,
            "on_chain_anchor": anchor,
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise CosmosSubmitError(f"Cosmos anchor HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise CosmosSubmitError(
            f"Cosmos REST unreachable at {url!r}: {exc.reason}. "
            "Start a local devnet or set TEGALCHAIN_SUBMITTER_BACKEND=mock."
        ) from exc

    for key in ("txhash", "tx_hash", "hash", "submit_ref", "ledger_ref"):
        value = payload.get(key)
        if value:
            return str(value)

    raise CosmosSubmitError(
        f"Cosmos anchor response missing txhash/submit_ref keys: {payload!r}"
    )
