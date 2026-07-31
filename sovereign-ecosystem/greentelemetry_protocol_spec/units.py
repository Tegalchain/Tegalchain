"""Approved base units for TP-101 measurement types (Section 2.3)."""

from __future__ import annotations

from .models import MeasurementType

MEASUREMENT_BASE_UNITS: dict[MeasurementType, tuple[str, ...]] = {
    MeasurementType.CO2E: ("kg CO2e", "kgCO2e", "tCO2e"),
    MeasurementType.CH4: ("kg", "g", "t"),
    MeasurementType.N2O: ("kg", "g", "t"),
    MeasurementType.ENERGY_KWH: ("kWh", "MWh", "Wh"),
    MeasurementType.ENERGY_MJ: ("MJ", "GJ", "kJ"),
    MeasurementType.WATER_M3: ("m3", "L", "ML"),
    MeasurementType.BIODIVERSITY: ("count", "ha", "m2"),
    MeasurementType.OFFSET_CREDIT: ("tCO2e", "credit"),
    MeasurementType.CUSTOM: (),  # any unit up to 16 chars when declared in metadata
}


def assert_measurement_unit(measurement_type: MeasurementType, unit: str) -> None:
    if measurement_type is MeasurementType.CUSTOM:
        if not unit or len(unit) > 16:
            raise ValueError("CUSTOM measurement requires unit string(1..16)")
        return
    allowed = MEASUREMENT_BASE_UNITS[measurement_type]
    if unit not in allowed:
        raise ValueError(
            f"unit {unit!r} not approved for {measurement_type.value}; "
            f"expected one of {allowed}"
        )
