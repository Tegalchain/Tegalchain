"""Submitter configuration (backend-agnostic)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .backends import SubmitterBackend, resolve_submitter_backend

ROOT = Path(__file__).resolve().parents[1]
ECOSYSTEM_ROOT = ROOT.parent
DEFAULT_DB = ROOT / "data" / "mint_queue.db"
DEFAULT_OUTBOX = ROOT / "data" / "outbox"
TX_PL = ECOSYSTEM_ROOT / "tegalchain-core" / "qortal" / "tools" / "tx.pl"

DEFAULT_QORTAL_SERVICE = "99"
DEFAULT_QORTAL_DATA_TYPE = "JSON"
DEFAULT_COSMOS_REST_URL = "http://localhost:1317"
DEFAULT_COSMOS_ANCHOR_PATH = "/tegalchain/gretelemetry/v1/anchor"


@dataclass(frozen=True, slots=True)
class SubmitterConfig:
    db_path: Path
    outbox_dir: Path
    backend: SubmitterBackend
    api_url: str
    privkey: str | None
    qortal_service: str
    qortal_data_type: str
    tx_pl_path: Path
    cosmos_rest_url: str
    cosmos_anchor_path: str
    cosmos_bearer_token: str | None

    @classmethod
    def from_env(cls) -> SubmitterConfig:
        privkey = os.environ.get("TEGALCHAIN_PRIVKEY")
        return cls(
            db_path=Path(os.environ.get("TEGALCHAIN_MINT_QUEUE_DB", str(DEFAULT_DB))),
            outbox_dir=Path(os.environ.get("TEGALCHAIN_OUTBOX_DIR", str(DEFAULT_OUTBOX))),
            backend=resolve_submitter_backend(privkey=privkey),
            api_url=os.environ.get("TEGALCHAIN_API_URL", "http://localhost:12391"),
            privkey=privkey,
            qortal_service=os.environ.get(
                "GREETELEMETRY_QORTAL_SERVICE", DEFAULT_QORTAL_SERVICE
            ),
            qortal_data_type=os.environ.get(
                "GREETELEMETRY_QORTAL_DATA_TYPE", DEFAULT_QORTAL_DATA_TYPE
            ),
            tx_pl_path=Path(os.environ.get("TEGALCHAIN_TX_PL", str(TX_PL))),
            cosmos_rest_url=os.environ.get(
                "TEGALCHAIN_COSMOS_REST_URL", DEFAULT_COSMOS_REST_URL
            ),
            cosmos_anchor_path=os.environ.get(
                "TEGALCHAIN_COSMOS_ANCHOR_PATH", DEFAULT_COSMOS_ANCHOR_PATH
            ),
            cosmos_bearer_token=os.environ.get("TEGALCHAIN_COSMOS_BEARER_TOKEN"),
        )
