"""Lab AI attester key material for TP-108 stubs."""

from __future__ import annotations

LAB_AI_ATTESTER_SECRET = b"sovereign-lab-ai-attester-v1"
DEFAULT_AI_ATTESTER_ID = "did:tegal:ai:zeegate-cdr-bandwidth-v1"
DEFAULT_MODEL_PROFILE = "zeegate-cdr-bandwidth-v1"


def resolve_ai_attester_secret(attester_id: str) -> bytes | None:
    """Return signing secret for a known lab AI attester."""
    if attester_id == DEFAULT_AI_ATTESTER_ID:
        return LAB_AI_ATTESTER_SECRET
    return None
