"""Zerocell Zeegate DePIN client — telecom telemetry producer."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import (  # noqa: E402
    GeoPoint,
    MeasurementType,
    Metrics,
    SourceType,
    SovereignNodeTelemetry,
    SystemType,
    Tp101GreenTelemetryRecord,
)
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_gretelemetry, validate_telemetry  # noqa: E402
from integrations.mint_worker.submit import submit_telemetry  # noqa: E402
from tegalchain.mint import MintResult, mint_from_telemetry  # noqa: E402

TelemetryFormat = Literal["legacy", "gtr_v1"]


@dataclass(frozen=True, slots=True)
class ZeegateClient:
    node_id: str
    signing_secret: bytes | None = None
    project_id: str | None = None
    binding_id: str | None = None

    def collect_bandwidth_bytes(self) -> int:
        """Hook for native Android/network instrumentation; stub for development."""
        return 1_048_576

    def build_telemetry(self, bandwidth_bytes: int | None = None) -> SovereignNodeTelemetry:
        bandwidth = (
            self.collect_bandwidth_bytes() if bandwidth_bytes is None else bandwidth_bytes
        )
        if bandwidth < 0:
            raise ValueError("telecom_bandwidth_bytes must be non-negative")

        unsigned = SovereignNodeTelemetry(
            node_id=self.node_id,
            timestamp=int(time.time()),
            system_type=SystemType.ZEEGATE_TELECOM,
            metrics=Metrics(telecom_bandwidth_bytes=bandwidth),
            signature="",
            project_id=self.project_id,
            binding_id=self.binding_id,
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
            project_id=unsigned.project_id,
            binding_id=unsigned.binding_id,
        )

    def build_gtr_v1(
        self,
        bandwidth_bytes: int | None = None,
        *,
        source_type: SourceType = SourceType.SENSOR,
        location: GeoPoint | None = None,
        gtr_id: str | None = None,
    ) -> Tp101GreenTelemetryRecord:
        """Build a native TP-101 GTR for Zeegate telecom bandwidth evidence."""
        bandwidth = (
            self.collect_bandwidth_bytes() if bandwidth_bytes is None else bandwidth_bytes
        )
        if bandwidth < 0:
            raise ValueError("telecom_bandwidth_bytes must be non-negative")

        return build_signed_tp101_gtr(
            source_id=self.node_id[:64],
            source_type=source_type,
            measurement_type=MeasurementType.CUSTOM,
            value=float(bandwidth),
            unit="bytes",
            gtr_id=gtr_id,
            location=location,
            metadata={
                "system_type": SystemType.ZEEGATE_TELECOM.value,
                "legacy_metric": "telecom_bandwidth_bytes",
                "producer": "zeegate_telemetry",
            },
            project_id=self.project_id,
            binding_id=self.binding_id,
            signing_secret=self.signing_secret,
        )

    def publish(
        self,
        bandwidth_bytes: int | None = None,
        mint_worker_url: str | None = None,
        *,
        telemetry_format: TelemetryFormat = "legacy",
        source_type: SourceType = SourceType.SENSOR,
        location: GeoPoint | None = None,
        gtr_id: str | None = None,
    ) -> dict[str, Any]:
        if telemetry_format == "gtr_v1":
            return self.publish_gtr_v1(
                bandwidth_bytes,
                mint_worker_url=mint_worker_url,
                source_type=source_type,
                location=location,
                gtr_id=gtr_id,
            )

        telemetry = self.build_telemetry(bandwidth_bytes)
        validate_telemetry(telemetry)
        payload = telemetry.to_dict()

        if mint_worker_url:
            return submit_telemetry(mint_worker_url, payload)

        mint_result: MintResult = mint_from_telemetry(telemetry)
        return {
            "telemetry": payload,
            "mint": mint_result.block_candidate,
        }

    def publish_gtr_v1(
        self,
        bandwidth_bytes: int | None = None,
        *,
        mint_worker_url: str | None = None,
        source_type: SourceType = SourceType.SENSOR,
        location: GeoPoint | None = None,
        gtr_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate and publish a canonical TP-101 GTR to the mint worker."""
        record = self.build_gtr_v1(
            bandwidth_bytes,
            source_type=source_type,
            location=location,
            gtr_id=gtr_id,
        )
        validated = validate_gretelemetry(record, signing_secret=self.signing_secret)
        payload = validated.tp101.to_dict()

        if mint_worker_url:
            return submit_telemetry(
                mint_worker_url,
                payload,
                use_tp101_records=True,
            )

        mint_result: MintResult = mint_from_telemetry(validated.legacy)
        return {
            "telemetry": payload,
            "gtr_id": validated.tp101.gtr_id,
            "mint": mint_result.block_candidate,
        }


def main() -> None:
    import os

    fmt: TelemetryFormat = (
        "gtr_v1" if os.environ.get("GREETELEMETRY_FORMAT", "").lower() == "gtr_v1" else "legacy"
    )
    client = ZeegateClient(node_id="zerocell-node-001")
    worker = os.environ.get("MINT_WORKER_URL")
    result = client.publish(mint_worker_url=worker, telemetry_format=fmt)
    print(result)


if __name__ == "__main__":
    main()
