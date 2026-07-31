"""JSON Schema validation for TP-108 attestation metadata."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "ai-attestation-spec" / "schema.json"


class AiAttestationValidationError(ValueError):
    """TP-108 metadata failed schema validation."""


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


def validate_tp108_metadata(payload: dict[str, Any]) -> None:
    """Validate a metadata.tp108 object."""
    try:
        jsonschema.validate(instance=payload, schema=load_schema())
    except jsonschema.ValidationError as exc:
        raise AiAttestationValidationError(str(exc.message)) from exc


def canonical_inputs_hash(public_inputs: dict[str, Any]) -> str:
    """SHA-256 (hex) of sorted-keys JSON per TP-108."""
    blob = json.dumps(public_inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
