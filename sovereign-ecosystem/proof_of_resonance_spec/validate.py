"""JSON Schema validation for TP-102 wire objects."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "proof-of-resonance-spec" / "schema.json"


class PorValidationError(ValueError):
    """TP-102 payload failed schema validation."""


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


def validate_por_payload(payload: dict[str, Any]) -> None:
    try:
        jsonschema.validate(instance=payload, schema=load_schema())
    except jsonschema.ValidationError as exc:
        raise PorValidationError(str(exc.message)) from exc
