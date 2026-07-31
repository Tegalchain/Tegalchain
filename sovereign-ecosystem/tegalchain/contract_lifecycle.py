"""Governed smart contract deployment lifecycle.

Package → Install → Approve → Commit → Active.
See docs/TEGALCHAIN.md#contract-lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


class LifecyclePhase(str, Enum):
    PACKAGE = "package"
    INSTALL = "install"
    APPROVE = "approve"
    COMMIT = "commit"
    ACTIVE = "active"


_VALID_TRANSITIONS: dict[LifecyclePhase, frozenset[LifecyclePhase]] = {
    LifecyclePhase.PACKAGE: frozenset({LifecyclePhase.INSTALL}),
    LifecyclePhase.INSTALL: frozenset({LifecyclePhase.APPROVE}),
    LifecyclePhase.APPROVE: frozenset({LifecyclePhase.COMMIT}),
    LifecyclePhase.COMMIT: frozenset({LifecyclePhase.ACTIVE}),
    LifecyclePhase.ACTIVE: frozenset(),
}


@dataclass(frozen=True, slots=True)
class ContractDefinition:
    name: str
    wasm_hash: str
    endorsement_policy_expr: str
    phase: LifecyclePhase = LifecyclePhase.PACKAGE
    org_approvals: frozenset[str] = frozenset()
    required_orgs: frozenset[str] = frozenset()

    def with_phase(self, phase: LifecyclePhase) -> ContractDefinition:
        allowed = _VALID_TRANSITIONS.get(self.phase, frozenset())
        if phase not in allowed:
            raise ValueError(
                f"invalid lifecycle transition {self.phase.value} → {phase.value}"
            )
        return replace(self, phase=phase)

    def record_org_approval(self, org_id: str) -> ContractDefinition:
        if self.phase is not LifecyclePhase.APPROVE:
            raise ValueError("org approval only valid in Approve phase")
        return replace(self, org_approvals=self.org_approvals | {org_id})

    def ready_to_commit(self) -> bool:
        if self.phase is not LifecyclePhase.APPROVE:
            return False
        if not self.required_orgs:
            return bool(self.org_approvals)
        return self.required_orgs.issubset(self.org_approvals)
