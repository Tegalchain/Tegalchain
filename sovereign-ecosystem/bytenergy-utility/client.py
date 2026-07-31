"""Bytenergy Utility client — prosumer electrical telemetry producer."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import (  # noqa: E402
    Metrics,
    SovereignNodeTelemetry,
    SystemType,
)
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_telemetry  # noqa: E402
from integrations.mint_worker.submit import submit_telemetry  # noqa: E402
from tegalchain.mint import MintResult, mint_from_telemetry  # noqa: E402


@dataclass(frozen=True, slots=True)
class BytenergyClient:
    node_id: str
    signing_secret: bytes | None = None

    def collect_generation_kwh(self) -> float:
        """Hook for smart-meter / inverter telemetry; stub for development."""
        return 3.42

    def build_telemetry(self, generation_kwh: float | None = None) -> SovereignNodeTelemetry:
        generation = (
            self.collect_generation_kwh() if generation_kwh is None else generation_kwh
        )
        if generation < 0:
            raise ValueError("energy_generation_kwh must be non-negative")

        unsigned = SovereignNodeTelemetry(
            node_id=self.node_id,
            timestamp=int(time.time()),
            system_type=SystemType.BYTENERGY_UTILITY,
            metrics=Metrics(energy_generation_kwh=generation),
            signature="",
        )
        canonical = unsigned_canonical_json(unsigned.to_dict())
        signature = (
            sign_payload(canonical, self.signing_secret)
            if self.signing_secret is not None
            else sign_payload(canonical)
        )

        return SovereignNodeTelemetry(
            node_id=unsigned.node_id,
            timestamp=unsigned.timestamp,
            system_type=unsigned.system_type,
            metrics=unsigned.metrics,
            signature=signature,
        )

    def publish(
        self,
        generation_kwh: float | None = None,
        mint_worker_url: str | None = None,
    ) -> dict[str, Any]:
        telemetry = self.build_telemetry(generation_kwh)
        validate_telemetry(telemetry)
        payload = telemetry.to_dict()

        if mint_worker_url:
            return submit_telemetry(mint_worker_url, payload)

        mint_result: MintResult = mint_from_telemetry(telemetry)
        return {
            "telemetry": payload,
            "mint": mint_result.block_candidate,
        }


def main() -> None:
    import os

    client = BytenergyClient(node_id="bytenergy-prosumer-001")
    worker = os.environ.get("MINT_WORKER_URL")
    result = client.publish(mint_worker_url=worker)
    print(result)


if __name__ == "__main__":
    main()
