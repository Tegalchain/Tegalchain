"""Contract best-practice validators for bridge and simulation code.

See docs/TEGALCHAIN.md#contract-best-practices.
"""

from __future__ import annotations

from typing import Any, Callable


class ContractValidationError(ValueError):
    pass


def require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{field_name} must be a non-empty string")
    return value


def require_non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractValidationError(f"{field_name} must be an integer")
    if value < 0:
        raise ContractValidationError(f"{field_name} must be non-negative")
    return value


def reject_external_oracle_fields(payload: dict[str, Any]) -> None:
    """Guard against non-deterministic external fetch markers in invoke args."""
    forbidden = {"http_url", "oracle_url", "random_seed", "wall_clock_now"}
    present = forbidden.intersection(payload.keys())
    if present:
        joined = ", ".join(sorted(present))
        raise ContractValidationError(
            f"non-deterministic external fields not allowed: {joined}"
        )


def assert_create_if_absent(
    state_exists: Callable[[str], bool],
    key: str,
) -> None:
    if state_exists(key):
        raise ContractValidationError(f"record already exists: {key}")
