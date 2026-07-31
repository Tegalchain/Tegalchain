"""TP-101 GTR binding to TP-103 ledger handoff.

Builds ledger-bound GreenTelemetry Records after oracle verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from greentelemetry_protocol_spec.gtr import (
    GreenTelemetryRecord,
    ReportingMode,
    TP101_STANDARD_ID,
    compute_gtr_hash,
    gtr_trust_score,
)
from greentelemetry_protocol_spec.models import Tp101GreenTelemetryRecord
from greentelemetry_protocol_spec.validate import ValidatedGreTelemetry

from .mint import MintResult, StateUpdate
from .por.score_gtr import score_gtr_for_por
from .tegalid_gate import NodeBinding


class GTRConsumer(str, Enum):
    """Downstream TP standards that consume verified GTRs."""

    GREEN_LEDGER = "TP-103"
    PROOF_OF_RESONANCE = "TP-102"
    TEGAL_DAO = "TP-106"


@dataclass(frozen=True, slots=True)
class LedgerBoundGTR:
    """GTR verified at the oracle edge and ready for GreenLedger anchor."""

    record: GreenTelemetryRecord
    state_update: StateUpdate
    block_candidate: dict[str, Any]
    reporting_mode: ReportingMode
    attestation_score: int | None
    consumers: tuple[GTRConsumer, ...]

    @property
    def tp101(self) -> Tp101GreenTelemetryRecord:
        return self.record.tp101

    def consumer_metadata(self) -> dict[str, Any]:
        """Routing hints for TP-103 archive, TP-102 attestation, TP-106 KPI feeds."""
        rfm = score_gtr_for_por(
            self.tp101,
            gtr_hash=self.record.record_hash,
            binding_attestation_score=self.attestation_score,
        )
        return {
            "gtr_id": self.tp101.gtr_id,
            "gtr_hash": self.record.record_hash,
            "protocol_standard": TP101_STANDARD_ID,
            "schema_version": self.tp101.schema_version,
            "measurement_type": self.tp101.measurement_type.value,
            "unit": self.tp101.unit,
            "value": self.tp101.value,
            "reporting_mode": self.reporting_mode.value,
            "binding_attestation_score": self.attestation_score,
            "trust_score": gtr_trust_score(self.tp101),
            "attestation_count": len(self.tp101.attestations),
            "consumers": {
                GTRConsumer.GREEN_LEDGER.value: {
                    "auditrail_record_type": self.block_candidate.get(
                        "auditrail_record_type", "GREETELEMETRY"
                    ),
                    "state_key": self.state_update.state_key,
                },
                GTRConsumer.PROOF_OF_RESONANCE.value: {
                    "rfm": rfm.to_dict(),
                    "binding_attestation_score": self.attestation_score,
                    "measurement_type": self.tp101.measurement_type.value,
                    "source_type": self.tp101.source_type.value,
                },
                GTRConsumer.TEGAL_DAO.value: {
                    "project_id": self.tp101.project_id,
                    "measurement_type": self.tp101.measurement_type.value,
                    "source_id": self.tp101.source_id,
                },
            },
        }


def build_ledger_bound_gtr(
    mint_result: MintResult,
    validated: ValidatedGreTelemetry,
    *,
    binding: NodeBinding | None = None,
    reporting_mode: ReportingMode = ReportingMode.STREAM,
) -> LedgerBoundGTR:
    """Wrap a mint result as a TP-101 GTR bound for TP-103 submission."""
    record = GreenTelemetryRecord.from_validated(validated.tp101, validated.legacy)
    gtr_hash = compute_gtr_hash(validated.tp101)
    block_candidate = dict(mint_result.block_candidate)
    block_candidate["gtr_id"] = validated.tp101.gtr_id
    block_candidate["gtr_hash"] = gtr_hash
    block_candidate["protocol_standard"] = TP101_STANDARD_ID
    block_candidate["schema_version"] = validated.tp101.schema_version
    block_candidate["reporting_mode"] = reporting_mode.value
    block_candidate["tp101_record"] = validated.tp101.to_dict()

    attestation_score = binding.attestation_score if binding is not None else None
    rfm = score_gtr_for_por(
        validated.tp101,
        gtr_hash=gtr_hash,
        binding_attestation_score=attestation_score,
    )
    block_candidate["tp102_rfm"] = rfm.to_dict()
    return LedgerBoundGTR(
        record=record,
        state_update=mint_result.state_update,
        block_candidate=block_candidate,
        reporting_mode=reporting_mode,
        attestation_score=attestation_score,
        consumers=(
            GTRConsumer.GREEN_LEDGER,
            GTRConsumer.PROOF_OF_RESONANCE,
            GTRConsumer.TEGAL_DAO,
        ),
    )
