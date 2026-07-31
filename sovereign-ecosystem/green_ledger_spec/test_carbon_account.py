"""Tests for TP-103 Carbon Account aggregation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from green_ledger_spec.carbon_account import aggregate_carbon_account  # noqa: E402
from green_ledger_spec.validate import validate_carbon_account_payload  # noqa: E402


def _gle(
    *,
    source_id: str = "plant-a",
    measurement_type: str = "CO2E",
    value: float = 100.0,
    unit: str = "kgCO2e",
    measurement_timestamp: str = "2026-07-15T10:00:00Z",
    archive_timestamp: str = "2026-07-15T10:05:00Z",
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "measurement_type": measurement_type,
        "value": value,
        "unit": unit,
        "measurement_timestamp": measurement_timestamp,
        "archive_timestamp": archive_timestamp,
    }


class CarbonAccountTests(unittest.TestCase):
    def test_aggregate_emissions_and_offsets(self) -> None:
        gles = [
            _gle(measurement_type="CO2E", value=100.0),
            _gle(measurement_type="OFFSET_CREDIT", value=25.0),
        ]
        account = aggregate_carbon_account(
            source_id="plant-a",
            period_start="2026-07-01T00:00:00Z",
            period_end="2026-07-31T23:59:59Z",
            gles=gles,
            expected_gtr_count=2,
        )
        payload = account.to_dict()
        validate_carbon_account_payload(payload)
        self.assertEqual(payload["gross_emissions_kgco2e"], 100.0)
        self.assertEqual(payload["offset_credits_kgco2e"], 25.0)
        self.assertEqual(payload["net_emissions_kgco2e"], 75.0)
        self.assertEqual(payload["data_completeness"], 1.0)

    def test_tco2e_normalisation(self) -> None:
        account = aggregate_carbon_account(
            source_id="plant-b",
            period_start="2026-07-01T00:00:00Z",
            period_end="2026-07-31T23:59:59Z",
            gles=[_gle(source_id="plant-b", value=1.0, unit="tCO2e")],
        )
        self.assertEqual(account.gross_emissions_kgco2e, 1000.0)


if __name__ == "__main__":
    unittest.main()
