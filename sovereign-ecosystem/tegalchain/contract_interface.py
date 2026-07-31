"""Smart contract invoke/query interface (in-process simulation).

Target runtime maps to CosmWasm ``execute`` / ``query``. State access via
``ctx.state`` — see docs/TEGALCHAIN.md#state-access-patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .state_access import ContractState


class ContractError(ValueError):
    pass


StateView = ContractState


@dataclass(frozen=True, slots=True)
class IdentityView:
    caller_id: str

    def get_id(self) -> str:
        return self.caller_id


@dataclass(frozen=True, slots=True)
class TransactionContext:
    state: StateView
    identity: IdentityView
    channel_id: str
    timestamp: int


@dataclass(frozen=True, slots=True)
class InvokeRequest:
    contract: str
    function: str
    args: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class QueryRequest:
    contract: str
    function: str
    args: tuple[Any, ...]


ContractHandler = Callable[[TransactionContext, tuple[Any, ...]], Any]


@dataclass
class InMemoryContract:
    """Register invoke/query handlers for deterministic simulation tests."""

    invokes: dict[str, ContractHandler] = field(default_factory=dict)
    queries: dict[str, ContractHandler] = field(default_factory=dict)

    def register_invoke(self, name: str, handler: ContractHandler) -> None:
        self.invokes[name] = handler

    def register_query(self, name: str, handler: ContractHandler) -> None:
        self.queries[name] = handler

    def invoke(self, ctx: TransactionContext, request: InvokeRequest) -> Any:
        handler = self.invokes.get(request.function)
        if handler is None:
            raise ContractError(f"unknown invoke function: {request.function!r}")
        return handler(ctx, request.args)

    def query(self, ctx: TransactionContext, request: QueryRequest) -> Any:
        handler = self.queries.get(request.function)
        if handler is None:
            raise ContractError(f"unknown query function: {request.function!r}")
        return handler(ctx, request.args)
