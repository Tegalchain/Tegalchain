"""Tegalchain Identity Registry — registered GTR source_id lookup."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_REGISTRY_FILE = ROOT / "data" / "source_registry.example.json"


class SourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


@dataclass(frozen=True, slots=True)
class RegisteredSource:
    source_id: str
    status: SourceStatus
    description: str = ""


class SourceRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._sources: dict[str, RegisteredSource] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            self._sources = {}
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        loaded: dict[str, RegisteredSource] = {}
        for entry in data.get("sources", []):
            source = RegisteredSource(
                source_id=str(entry["source_id"]),
                status=SourceStatus(str(entry.get("status", "ACTIVE"))),
                description=str(entry.get("description", "")),
            )
            loaded[source.source_id] = source
        self._sources = loaded

    def get(self, source_id: str) -> RegisteredSource | None:
        return self._sources.get(source_id)

    def is_registered(self, source_id: str) -> bool:
        source = self.get(source_id)
        return source is not None and source.status is SourceStatus.ACTIVE


def get_source_registry_file() -> Path:
    return Path(os.environ.get("TEGALID_SOURCE_REGISTRY_FILE", str(DEFAULT_SOURCE_REGISTRY_FILE)))


def resolve_source_registry() -> SourceRegistry:
    return SourceRegistry(get_source_registry_file())


class SourceRegistryError(PermissionError):
    """Raised when source_id is not registered for GTR submission."""


def assert_source_registered(source_id: str) -> RegisteredSource:
    """TP-101: source_id MUST be registered before GTR submission."""
    registry = resolve_source_registry()
    source = registry.get(source_id)
    if source is None:
        raise SourceRegistryError(
            f"source_id {source_id!r} is not registered in the Tegalchain Identity Registry"
        )
    if source.status is not SourceStatus.ACTIVE:
        raise SourceRegistryError(
            f"source_id {source_id!r} registry status is {source.status.value}, not ACTIVE"
        )
    return source


def require_source_registry() -> bool:
    raw = os.environ.get("TEGALCHAIN_REQUIRE_SOURCE_REGISTRY", "").lower()
    if raw in {"1", "true", "yes"}:
        return True
    from .tegalid_gate import get_identity_mode, IdentityMode

    return get_identity_mode() is IdentityMode.TEGALID
