"""Dispatch TELEMETRY_MINT proposals to the configured submit backend."""

from __future__ import annotations

from typing import Any

from .backends import SubmitterBackend
from .config import SubmitterConfig
from .cosmos import submit_to_cosmos
from .mock import mock_submit_ref
from .qortal import submit_to_qortal


def submit_block_candidate(
    block_candidate: dict[str, Any],
    config: SubmitterConfig,
    *,
    queue_id: int,
) -> str:
    """Return chain submit reference (tx hash / lab mock id)."""
    if config.backend is SubmitterBackend.MOCK:
        return mock_submit_ref(block_candidate, queue_id=queue_id)
    if config.backend is SubmitterBackend.COSMOS:
        return submit_to_cosmos(
            block_candidate,
            rest_url=config.cosmos_rest_url,
            anchor_path=config.cosmos_anchor_path,
            bearer_token=config.cosmos_bearer_token,
        )
    if config.backend is SubmitterBackend.QORTAL:
        return submit_to_qortal(block_candidate, config)
    raise RuntimeError(f"backend {config.backend.value!r} does not submit to chain")
