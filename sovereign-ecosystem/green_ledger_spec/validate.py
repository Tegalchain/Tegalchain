"""JSON Schema validation for TP-103 wire objects."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "green-ledger-spec" / "schema.json"


class GleValidationError(ValueError):
    """TP-103 payload failed schema validation."""


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


def _validate(payload: dict[str, Any]) -> None:
    try:
        jsonschema.validate(instance=payload, schema=load_schema())
    except jsonschema.ValidationError as exc:
        raise GleValidationError(str(exc.message)) from exc


def validate_gle_payload(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "1.0" or "gle_id" not in payload:
        raise GleValidationError("not a GreenLedger Entry payload")
    _validate(payload)


def validate_carbon_account_payload(payload: dict[str, Any]) -> None:
    if "gross_emissions_kgco2e" not in payload:
        raise GleValidationError("not a Carbon Account payload")
    _validate(payload)
