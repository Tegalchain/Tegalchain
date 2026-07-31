"""TP-103 Carbon Account — materialised per-source emissions aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable

TP103_CARBON_ACCOUNT_VERSION = "1.0"

# Normalise offset / emission units to kg CO2e.
_KG_CO2E_UNITS = {"kg", "kgco2e", "kg co2e"}
_TCO2E_UNITS = {"tco2e", "t", "tonnes", "tonne"}


@dataclass(frozen=True, slots=True)
class CarbonAccount:
    source_id: str
    period_start: str
    period_end: str
    gross_emissions_kgco2e: float
    offset_credits_kgco2e: float
    net_emissions_kgco2e: float
    data_completeness: float
    last_updated: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "gross_emissions_kgco2e": round(self.gross_emissions_kgco2e, 6),
            "offset_credits_kgco2e": round(self.offset_credits_kgco2e, 6),
            "net_emissions_kgco2e": round(self.net_emissions_kgco2e, 6),
            "data_completeness": round(self.data_completeness, 4),
            "last_updated": self.last_updated,
            "schema_version": TP103_CARBON_ACCOUNT_VERSION,
            "protocol_standard": "TP-103",
        }


def _to_kgco2e(value: float, unit: str) -> float:
    normalised = unit.strip().lower().replace(" ", "")
    if normalised in _TCO2E_UNITS or normalised == "tco2e":
        return value * 1000.0
    if normalised in _KG_CO2E_UNITS or normalised.endswith("co2e"):
        return value
    if normalised in {"g", "gram", "grams"}:
        return value / 1000.0
    return value


def _gle_in_period(gle: dict[str, Any], period_start: str, period_end: str) -> bool:
    ts = str(gle.get("measurement_timestamp", ""))
    return period_start <= ts <= period_end


def _contribution_kgco2e(gle: dict[str, Any]) -> tuple[float, float]:
    """Return (emissions_kg, offsets_kg) for one GLE."""
    measurement = str(gle.get("measurement_type", ""))
    value = float(gle.get("value", 0.0))
    unit = str(gle.get("unit", ""))
    kg = _to_kgco2e(abs(value), unit)
    if measurement == "OFFSET_CREDIT":
        return 0.0, kg
    if measurement in {"CO2E", "CH4", "N2O"}:
        return kg, 0.0
    return 0.0, 0.0


def aggregate_carbon_account(
    *,
    source_id: str,
    period_start: str,
    period_end: str,
    gles: Iterable[dict[str, Any]],
    expected_gtr_count: int | None = None,
) -> CarbonAccount:
    """Build a materialised Carbon Account from archived GLE rows."""
    gross = 0.0
    offsets = 0.0
    received = 0
    last_updated = period_start
    for gle in gles:
        if str(gle.get("source_id")) != source_id:
            continue
        if not _gle_in_period(gle, period_start, period_end):
            continue
        emissions, credit = _contribution_kgco2e(gle)
        gross += emissions
        offsets += credit
        received += 1
        ts = str(gle.get("archive_timestamp") or gle.get("measurement_timestamp", ""))
        if ts > last_updated:
            last_updated = ts

    if received == 0:
        last_updated = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    if expected_gtr_count is not None and expected_gtr_count > 0:
        completeness = min(1.0, received / expected_gtr_count)
    else:
        completeness = 1.0 if received > 0 else 0.0

    return CarbonAccount(
        source_id=source_id,
        period_start=period_start,
        period_end=period_end,
        gross_emissions_kgco2e=gross,
        offset_credits_kgco2e=offsets,
        net_emissions_kgco2e=max(0.0, gross - offsets),
        data_completeness=completeness,
        last_updated=last_updated,
    )
