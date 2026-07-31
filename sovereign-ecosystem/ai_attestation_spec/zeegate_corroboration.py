"""Zeegate CDR ↔ bandwidth corroboration (TP-108 reference profile)."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_attestation_spec.keys import DEFAULT_MODEL_PROFILE  # noqa: E402
from ai_attestation_spec.validate import canonical_inputs_hash  # noqa: E402

DEFAULT_CDR_FIXTURE = (
    ROOT / "zeegate-cloud" / "cdr_adapter" / "fixtures" / "sample_cdr.csv"
)
# Lab pairing: phase7 ingest uses 1 MiB; sample CDR billsec is 85.
LAB_BYTES_PER_BILLSEC = 1048576 / 85.0


class CorroborationVerdict(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class CorroborationResult:
    verdict: CorroborationVerdict
    score: float
    bandwidth_bytes: float
    billsec: int
    ratio: float
    public_inputs: dict[str, Any]
    inputs_hash: str


def bandwidth_bytes_from_tp101(tp101: dict[str, Any]) -> float:
    """Extract edge bandwidth bytes from a Zeegate-normalized TP-101 record."""
    metadata = tp101.get("metadata") or {}
    if metadata.get("legacy_metric") == "telecom_bandwidth_bytes":
        return float(tp101["value"])
    if tp101.get("unit") == "bytes":
        return float(tp101["value"])
    raise ValueError("TP-101 record is not a Zeegate bandwidth GTR")


def load_cdr_billsec(
    fixture_path: Path,
    *,
    sip_extension: str = "edge001",
) -> tuple[int, str]:
    """Aggregate billsec for rows matching sip_extension; hash fixture bytes."""
    total_billsec = 0
    text = fixture_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = [field.strip().strip('"') for field in stripped.split(",")]
        if len(fields) < 7:
            continue
        caller = fields[1]
        if caller != sip_extension and sip_extension not in caller:
            continue
        total_billsec += int(fields[6] or "0")
    if total_billsec <= 0:
        raise ValueError(f"no billsec found for {sip_extension!r} in {fixture_path}")
    cdr_sha256 = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    return total_billsec, cdr_sha256


def evaluate_corroboration(
    bandwidth_bytes: float,
    billsec: int,
    *,
    bytes_per_billsec: float = LAB_BYTES_PER_BILLSEC,
) -> tuple[CorroborationVerdict, float, float]:
    """Return verdict, score, and implied/billed ratio per TP-108 bands."""
    if billsec <= 0:
        return CorroborationVerdict.FAIL, 0.0, 0.0
    implied_billsec = bandwidth_bytes / bytes_per_billsec
    ratio = implied_billsec / float(billsec)
    if 0.5 <= ratio <= 2.0:
        verdict = CorroborationVerdict.PASS
        score = max(0.0, min(1.0, 1.0 - abs(ratio - 1.0)))
    elif 0.25 <= ratio <= 4.0:
        verdict = CorroborationVerdict.WARN
        score = max(0.0, 0.5 - abs(ratio - 1.0) * 0.1)
    else:
        verdict = CorroborationVerdict.FAIL
        score = 0.0
    return verdict, score, ratio


def build_corroboration_result(
    tp101: dict[str, Any],
    *,
    billsec: int,
    cdr_sha256: str,
    binding_id: str | None = None,
    window_start: str | None = None,
    window_end: str | None = None,
    model_profile: str = DEFAULT_MODEL_PROFILE,
) -> CorroborationResult:
    bandwidth_bytes = bandwidth_bytes_from_tp101(tp101)
    verdict, score, ratio = evaluate_corroboration(bandwidth_bytes, billsec)
    public_inputs: dict[str, Any] = {
        "binding_id": binding_id or tp101.get("binding_id") or "",
        "cdr_sha256": cdr_sha256,
        "edge_source_id": str(tp101["source_id"]),
        "gtr_id": str(tp101["gtr_id"]),
        "model_profile": model_profile,
    }
    if window_start:
        public_inputs["window_start"] = window_start
    if window_end:
        public_inputs["window_end"] = window_end
    inputs_hash = canonical_inputs_hash(public_inputs)
    return CorroborationResult(
        verdict=verdict,
        score=score,
        bandwidth_bytes=bandwidth_bytes,
        billsec=billsec,
        ratio=ratio,
        public_inputs=public_inputs,
        inputs_hash=inputs_hash,
    )


def corroborate_from_fixture(
    tp101: dict[str, Any],
    fixture_path: Path | None = None,
    *,
    sip_extension: str = "edge001",
) -> CorroborationResult:
    path = fixture_path or DEFAULT_CDR_FIXTURE
    billsec, cdr_sha256 = load_cdr_billsec(path, sip_extension=sip_extension)
    return build_corroboration_result(
        tp101,
        billsec=billsec,
        cdr_sha256=cdr_sha256,
    )
