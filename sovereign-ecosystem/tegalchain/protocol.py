"""Tegalchain protocol phases and shared constants.

Maps documented lifecycle in docs/TEGALCHAIN.md to typed enums for the Phase 1 bridge.
"""

from __future__ import annotations

from enum import Enum


class TransactionPhase(str, Enum):
    """Five-phase transaction lifecycle."""

    PROPOSAL = "proposal"
    SIMULATION = "simulation"
    ENDORSEMENT_COLLECTION = "endorsement_collection"
    ORDERING = "ordering"
    VALIDATION_AND_COMMIT = "validation_and_commit"


class NetworkPlane(str, Enum):
    """Consensus vs data vs ingress planes."""

    CONSENSUS = "consensus"
    DATA = "data"
    INGRESS = "ingress"
