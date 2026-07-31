"""Adapter-normalized CDR → TP-101 GTR for mint worker ingress."""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import MeasurementType, SourceType, Tp101GreenTelemetryRecord  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_gretelemetry  # noqa: E402
from integrations.mint_worker.submit import submit_telemetry  # noqa: E402

from .models import CdrRow  # noqa: E402
from .parse import call_id_hash, fs_stamp_to_iso8601  # noqa: E402
from .resolve import resolve_cdr_source  # noqa: E402


@dataclass(frozen=True, slots=True)
class CdrAdapterConfig:
    bindings_file: Path | None = None
    fallback_source_id: str | None = None
    mint_worker_url: str | None = None
    bearer_token: str | None = None


class CdrAdapter:
    """Normalize FreeSWITCH CDR summaries into signed GTR v1 records."""

    def __init__(self, config: CdrAdapterConfig | None = None) -> None:
        self.config = config or CdrAdapterConfig()

    def source_for_row(self, row: CdrRow) -> tuple[str, str | None, str | None, bytes | None]:
        return resolve_cdr_source(
            row.caller_id_number,
            bindings_file=self.config.bindings_file,
            fallback_source_id=self.config.fallback_source_id,
        )

    def build_gtr(self, row: CdrRow) -> Tp101GreenTelemetryRecord:
        source_id, project_id, binding_id, signing_secret = self.source_for_row(row)
        measurement_time = fs_stamp_to_iso8601(row.end_stamp)
        return build_signed_tp101_gtr(
            source_id=source_id[:64],
            source_type=SourceType.API,
            measurement_type=MeasurementType.CUSTOM,
            value=float(row.total_bytes),
            unit="bytes",
            gtr_id=str(uuid.uuid4()),
            timestamp=measurement_time,
            metadata={
                "system_type": "ZEEGATE_TELECOM",
                "evidence_kind": "CDR",
                "adapter": "zeegate_cdr",
                "legacy_metric": "telecom_bandwidth_bytes",
                "call_id_hash": call_id_hash(row.uuid),
                "duration_sec": row.duration,
                "billsec": row.billsec,
                "hangup_cause": row.hangup_cause,
                "read_bytes": row.read_bytes,
                "write_bytes": row.write_bytes,
                "sip_extension": row.caller_id_number,
                "destination_ext": row.destination_number,
            },
            project_id=project_id,
            binding_id=binding_id,
            signing_secret=signing_secret,
        )

    def publish_row(self, row: CdrRow) -> dict[str, Any]:
        record = self.build_gtr(row)
        validated = validate_gretelemetry(record, signing_secret=self.source_for_row(row)[3])
        payload = validated.tp101.to_dict()
        if not self.config.mint_worker_url:
            return {"gtr_id": validated.tp101.gtr_id, "record": payload, "status": "built"}
        return submit_telemetry(
            self.config.mint_worker_url,
            payload,
            bearer_token=self.config.bearer_token,
            use_tp101_records=True,
        )
