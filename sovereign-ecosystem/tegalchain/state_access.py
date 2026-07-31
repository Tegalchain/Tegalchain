"""Smart contract state access API.

Contracts interact with ledger state through ``state.get``, ``put``, ``delete``,
``get_range``, ``get_query`` (CouchDB), and ``get_history``.
See docs/TEGALCHAIN.md#state-access-patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .state import StateDatabaseBackend


class StateAccessError(ValueError):
    pass


class RichQueryNotSupportedError(StateAccessError):
    """Raised when ``get_query`` is used without a CouchDB backend."""


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    value: Any


@dataclass
class ContractState:
    """In-process state API mirroring the Tegalchain contract state surface."""

    backend: StateDatabaseBackend = StateDatabaseBackend.LEVELDB
    _store: dict[str, Any] = field(default_factory=dict)
    _history: dict[str, list[HistoryEntry]] = field(default_factory=dict)

    def exists(self, key: str) -> bool:
        return key in self._store

    def get(self, key: str) -> Any:
        return self._store.get(key)

    def put(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._record_history(key, value)

    def delete(self, key: str) -> None:
        if key not in self._store:
            return
        del self._store[key]
        self._record_history(key, None)

    def get_range(self, start: str, end: str) -> list[tuple[str, Any]]:
        """Return ``[start, end)`` key-range entries in sorted key order."""
        if start > end:
            raise StateAccessError("get_range start must be <= end")
        return sorted(
            (key, value)
            for key, value in self._store.items()
            if start <= key < end
        )

    def get_query(self, expression: dict[str, Any]) -> list[dict[str, Any]]:
        """Rich document query — CouchDB backend only."""
        if self.backend is not StateDatabaseBackend.COUCHDB:
            raise RichQueryNotSupportedError(
                "state.get_query requires CouchDB state database backend"
            )
        selector = expression.get("selector")
        if not isinstance(selector, dict):
            raise StateAccessError("get_query expression must include selector dict")

        matches: list[dict[str, Any]] = []
        for key, value in self._store.items():
            document = value if isinstance(value, dict) else {"_key": key, "value": value}
            if _matches_selector(document, selector):
                matches.append({"_key": key, **document})
        return matches

    def get_history(self, key: str) -> list[HistoryEntry]:
        """Full history of committed values for a key."""
        return list(self._history.get(key, []))

    def _record_history(self, key: str, value: Any) -> None:
        self._history.setdefault(key, []).append(HistoryEntry(value=value))


def _matches_selector(document: dict[str, Any], selector: dict[str, Any]) -> bool:
    for field_name, expected in selector.items():
        if document.get(field_name) != expected:
            return False
    return True
