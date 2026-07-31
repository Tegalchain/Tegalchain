"""Lab mock submitter — deterministic ledger_ref without a chain node."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def mock_submit_ref(
    block_candidate: dict[str, Any],
    *,
    queue_id: int | None = None,
) -> str:
    """Return a stable lab submit reference derived from the anchor payload."""
    canonical = json.dumps(block_candidate, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    suffix = f"-Q{queue_id:06d}" if queue_id is not None else ""
    return f"LABMOCK-{digest[:40].upper()}{suffix}"
