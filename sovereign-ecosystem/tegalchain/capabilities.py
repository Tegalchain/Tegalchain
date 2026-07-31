"""Protocol capability flags and safe upgrade sequencing.

See docs/TEGALCHAIN.md#protocol-upgrades.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .network_config import (
    ChannelConfig,
    ConfigUpdateKind,
    ConfigUpdateProposal,
    ConfigUpdateSignature,
    ConfigUpdateWorkflow,
    NetworkConfigError,
)


class CapabilityUpgradeError(NetworkConfigError):
    pass


# Minimum bridge software versions that understand each capability flag.
CAPABILITY_MIN_VERSION: dict[str, str] = {
    "gretelemetry_oracle": "1.0.0",
    "zk_evidence_optional": "1.2.0",
    "multi_org_endorsement": "1.3.0",
}


@dataclass(frozen=True, slots=True)
class NodeVersionReport:
    node_id: str
    software_version: str
    supported_capabilities: frozenset[str]


def capability_is_active(config: ChannelConfig, capability: str) -> bool:
    return capability in config.capabilities.features


def assert_capability_active(config: ChannelConfig, capability: str) -> None:
    if not capability_is_active(config, capability):
        raise CapabilityUpgradeError(f"capability not active on channel: {capability!r}")


def verify_all_nodes_support_capability(
    capability: str,
    reports: Sequence[NodeVersionReport],
) -> None:
    if not reports:
        raise CapabilityUpgradeError("no node version reports supplied")
    for report in reports:
        if capability not in report.supported_capabilities:
            raise CapabilityUpgradeError(
                f"node {report.node_id!r} software {report.software_version!r} "
                f"does not support capability {capability!r}"
            )


def propose_enable_capability(
    config: ChannelConfig,
    *,
    capability: str,
    proposer_admin_org: str,
) -> ConfigUpdateProposal:
    config.assert_org_member(proposer_admin_org)
    if capability in config.capabilities.features:
        raise CapabilityUpgradeError(f"capability already enabled: {capability!r}")
    return ConfigUpdateProposal(
        channel_id=config.channel_id,
        kind=ConfigUpdateKind.ENABLE_CAPABILITY,
        target_org_id=capability,
        proposer_admin_org=proposer_admin_org,
    )


@dataclass
class CapabilityUpgradeWorkflow:
    """Upgrade sequence: nodes upgrade → verify → config proposal → activate."""

    config_workflow: ConfigUpdateWorkflow
    node_reports: tuple[NodeVersionReport, ...] = ()

    def propose_enable(self, capability: str, proposer: str) -> ConfigUpdateProposal:
        verify_all_nodes_support_capability(capability, self.node_reports)
        return propose_enable_capability(
            self.config_workflow.history.current(),
            capability=capability,
            proposer_admin_org=proposer,
        )

    def commit_enable(
        self,
        capability: str,
        proposer: str,
        signatures: tuple[ConfigUpdateSignature, ...],
    ) -> ChannelConfig:
        proposal = self.propose_enable(capability, proposer)
        return self.config_workflow.commit_proposal(proposal, signatures)
