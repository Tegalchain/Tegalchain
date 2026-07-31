"""Zeegate cloud CDR → TP-101 GTR adapter (Phase 2)."""

from cdr_adapter.adapter import CdrAdapter, CdrAdapterConfig
from cdr_adapter.models import CdrRow
from cdr_adapter.watcher import process_cdr_directory

__all__ = [
    "CdrAdapter",
    "CdrAdapterConfig",
    "CdrRow",
    "process_cdr_directory",
]
