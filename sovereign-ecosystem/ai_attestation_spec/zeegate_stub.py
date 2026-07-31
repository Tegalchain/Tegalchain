"""CLI: Zeegate CDR ↔ bandwidth corroboration stub (TP-108)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai_attestation_spec.attestation import (  # noqa: E402
    build_third_party_attestation,
    tp108_metadata_from_corroboration,
)
from ai_attestation_spec.keys import DEFAULT_AI_ATTESTER_ID, DEFAULT_MODEL_PROFILE  # noqa: E402
from ai_attestation_spec.zeegate_corroboration import corroborate_from_fixture  # noqa: E402
from integrations.mint_worker.submit import append_gtr_attestation, get_gtr_record  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402


def resolve_gtr_id(explicit: str) -> str:
    if explicit:
        return explicit
    db_path = Path(
        os.environ.get(
            "TEGALCHAIN_MINT_QUEUE_DB",
            ROOT / "tegalchain" / "data" / "mint_queue.db",
        )
    )
    store = MintQueueStore(db_path)
    for row in store.fetch_recent(limit=50):
        tp101 = row.block_candidate.get("tp101_record") or {}
        if tp101.get("source_id") == "did:tegal:LABEDGE001":
            gtr_id = row.gtr_id or tp101.get("gtr_id")
            if gtr_id:
                return str(gtr_id)
    raise SystemExit(
        "ERROR: no gtr_id provided and no did:tegal:LABEDGE001 record in mint queue"
    )


def main() -> None:
    mint_url = os.environ.get("MINT_WORKER_URL", "http://127.0.0.1:8090")
    gtr_id = resolve_gtr_id(os.environ.get("PHASE8_GTR_ID", "").strip())
    bearer = os.environ.get("PHASE8_BEARER_TOKEN", "").strip() or None
    fixture = Path(
        os.environ.get(
            "ZEEGATE_CDR_FIXTURE",
            ROOT / "zeegate-cloud" / "cdr_adapter" / "fixtures" / "sample_cdr.csv",
        )
    )

    fetched = get_gtr_record(mint_url, gtr_id, bearer_token=bearer)
    tp101 = fetched.get("record") or {}
    if not tp101:
        raise SystemExit(f"ERROR: empty TP-101 record for gtr_id={gtr_id}")

    result = corroborate_from_fixture(tp101, fixture)
    tp108 = tp108_metadata_from_corroboration(result, model_profile=DEFAULT_MODEL_PROFILE)
    attestation = build_third_party_attestation(
        tp101,
        tp108=tp108,
        attester_id=DEFAULT_AI_ATTESTER_ID,
        confidence=min(0.95, max(0.5, result.score)),
    )

    print(f"gtr_id={gtr_id} verdict={result.verdict.value} ratio={result.ratio:.3f}")
    print(f"inputs_hash={result.inputs_hash}")
    updated = append_gtr_attestation(mint_url, gtr_id, attestation, bearer_token=bearer)
    attestations = updated.get("attestations") or []
    tp108_rows = [
        att.get("metadata", {}).get("tp108")
        for att in attestations
        if att.get("attester_type") == "THIRD_PARTY"
    ]
    print(json.dumps({"attestation_count": len(attestations), "tp108": tp108_rows}, indent=2))
    print("OK: Phase 8 AI corroboration attestation appended")


if __name__ == "__main__":
    main()
