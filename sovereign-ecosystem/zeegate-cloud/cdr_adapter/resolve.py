"""Resolve SIP lab extensions to gretelemetry source_id via tegalid bindings."""

from __future__ import annotations

import json
from pathlib import Path


def load_sip_user_map(bindings_file: Path) -> dict[str, dict[str, str]]:
    """Map sip_user → {source_id, project_id, binding_id, hmac_secret_hex}."""
    if not bindings_file.is_file():
        return {}
    data = json.loads(bindings_file.read_text(encoding="utf-8"))
    mapping: dict[str, dict[str, str]] = {}
    for entry in data.get("bindings", []):
        sip_user = str(entry.get("sip_user", "")).strip()
        if not sip_user:
            continue
        mapping[sip_user] = {
            "source_id": str(entry["did"]),
            "project_id": str(entry.get("project_id", "")),
            "binding_id": str(entry.get("binding_id", "")),
            "hmac_secret_hex": str(entry.get("telemetry_hmac_secret_hex", "")),
        }
    return mapping


def resolve_cdr_source(
    sip_extension: str,
    *,
    bindings_file: Path | None = None,
    fallback_source_id: str | None = None,
) -> tuple[str, str | None, str | None, bytes | None]:
    """Return (source_id, project_id, binding_id, signing_secret)."""
    if bindings_file is not None:
        entry = load_sip_user_map(bindings_file).get(sip_extension)
        if entry is not None:
            secret = bytes.fromhex(entry["hmac_secret_hex"]) if entry["hmac_secret_hex"] else None
            project_id = entry["project_id"] or None
            binding_id = entry["binding_id"] or None
            return entry["source_id"], project_id, binding_id, secret
    if fallback_source_id:
        return fallback_source_id, None, None, None
    return sip_extension, None, None, None
