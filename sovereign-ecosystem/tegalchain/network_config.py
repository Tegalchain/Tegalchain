"""Channel network configuration (config block) model.

Every channel has a genesis config block (block 0) and a history of configuration
updates. Config changes follow a policy-gated proposal workflow.
See docs/TEGALCHAIN.md#network-configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

from .endorsement import ORACLE_PEER_ID
from .access_control import acl_pairs_from_rules, greenledger_system_acl_rules, merge_acl_rules


class NetworkConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OrgMSPDefinition:
    """Organisation MSP material required to join a channel."""

    org_id: str
    msp_id: str
    ca_root_certificate_pem: str


@dataclass(frozen=True, slots=True)
class ChannelMembership:
    org_id: str
    msp_id: str
    ca_root_certificate_pem: str = ""

    @classmethod
    def from_msp_definition(cls, definition: OrgMSPDefinition) -> ChannelMembership:
        return cls(
            org_id=definition.org_id,
            msp_id=definition.msp_id,
            ca_root_certificate_pem=definition.ca_root_certificate_pem,
        )


@dataclass(frozen=True, slots=True)
class OrderingParameters:
    orderer_count: int
    max_block_size_bytes: int
    batch_timeout_ms: int


@dataclass(frozen=True, slots=True)
class ApplicationParameters:
    default_endorsement_policy: str
    access_control_list: frozenset[str] = frozenset()
    system_acl: frozenset[tuple[str, str]] = frozenset()


@dataclass(frozen=True, slots=True)
class ChannelCapabilities:
    protocol_version: str
    features: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class ModificationPolicy:
    """Admin signatures required to commit a config update (OutOf-style)."""

    required_admin_orgs: frozenset[str]
    threshold: int

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise NetworkConfigError("modification policy threshold must be at least 1")
        if self.threshold > len(self.required_admin_orgs):
            raise NetworkConfigError("threshold exceeds admin org count")

    def satisfied_by(self, signer_orgs: frozenset[str]) -> bool:
        allowed = self.required_admin_orgs
        matched = sum(1 for org in signer_orgs if org in allowed)
        return matched >= self.threshold


@dataclass(frozen=True, slots=True)
class ChannelConfig:
    """Config block snapshot for a channel at a given sequence."""

    channel_id: str
    sequence: int
    membership: tuple[ChannelMembership, ...]
    ordering: OrderingParameters
    application: ApplicationParameters
    capabilities: ChannelCapabilities

    def org_ids(self) -> frozenset[str]:
        return frozenset(member.org_id for member in self.membership)

    def assert_org_member(self, org_id: str) -> None:
        if org_id not in self.org_ids():
            raise NetworkConfigError(f"organisation not on channel: {org_id!r}")

    def membership_index(self) -> dict[str, ChannelMembership]:
        return {member.org_id: member for member in self.membership}


class ConfigUpdateKind(str, Enum):
    ADD_ORG = "add_org"
    REMOVE_ORG = "remove_org"
    ENABLE_CAPABILITY = "enable_capability"
    UPDATE_ACL = "update_acl"


@dataclass(frozen=True, slots=True)
class ConfigUpdateProposal:
    """Describes a desired channel configuration change."""

    channel_id: str
    kind: ConfigUpdateKind
    target_org_id: str
    proposer_admin_org: str
    msp_definition: OrgMSPDefinition | None = None
    acl_update: dict[str, frozenset[str]] | None = None


@dataclass(frozen=True, slots=True)
class ConfigUpdateSignature:
    admin_org: str
    signature: str


@dataclass
class ChannelConfigHistory:
    """Genesis config (block 0) plus ordered configuration updates."""

    genesis: ChannelConfig
    updates: list[ChannelConfig] = field(default_factory=list)
    removed_orgs: set[str] = field(default_factory=set)

    def current(self) -> ChannelConfig:
        if self.updates:
            return self.updates[-1]
        return self.genesis

    def history(self) -> tuple[ChannelConfig, ...]:
        return (self.genesis, *tuple(self.updates))

    def is_org_active(self, org_id: str) -> bool:
        return org_id in self.current().org_ids() and org_id not in self.removed_orgs

    def apply_update(self, update: ChannelConfig) -> None:
        current = self.current()
        if update.channel_id != current.channel_id:
            raise NetworkConfigError("config update channel_id mismatch")
        if update.sequence != current.sequence + 1:
            raise NetworkConfigError(
                f"config sequence must increment: expected {current.sequence + 1}, "
                f"got {update.sequence}"
            )
        removed = current.org_ids() - update.org_ids()
        self.removed_orgs.update(removed)
        self.updates.append(update)


def default_modification_policy(config: ChannelConfig) -> ModificationPolicy:
    admins = config.org_ids()
    threshold = max(1, (len(admins) + 1) // 2)
    return ModificationPolicy(required_admin_orgs=admins, threshold=threshold)


def propose_add_org(
    config: ChannelConfig,
    *,
    msp_definition: OrgMSPDefinition,
    proposer_admin_org: str,
) -> ConfigUpdateProposal:
    config.assert_org_member(proposer_admin_org)
    if msp_definition.org_id in config.org_ids():
        raise NetworkConfigError(f"organisation already on channel: {msp_definition.org_id}")
    return ConfigUpdateProposal(
        channel_id=config.channel_id,
        kind=ConfigUpdateKind.ADD_ORG,
        target_org_id=msp_definition.org_id,
        proposer_admin_org=proposer_admin_org,
        msp_definition=msp_definition,
    )


def propose_remove_org(
    config: ChannelConfig,
    *,
    org_id: str,
    proposer_admin_org: str,
) -> ConfigUpdateProposal:
    config.assert_org_member(proposer_admin_org)
    if org_id not in config.org_ids():
        raise NetworkConfigError(f"organisation not on channel: {org_id!r}")
    if org_id == proposer_admin_org and len(config.membership) == 1:
        raise NetworkConfigError("cannot remove the last organisation from channel")
    return ConfigUpdateProposal(
        channel_id=config.channel_id,
        kind=ConfigUpdateKind.REMOVE_ORG,
        target_org_id=org_id,
        proposer_admin_org=proposer_admin_org,
    )


def propose_update_acl(
    config: ChannelConfig,
    *,
    acl_update: dict[str, frozenset[str]],
    proposer_admin_org: str,
) -> ConfigUpdateProposal:
    config.assert_org_member(proposer_admin_org)
    if not acl_update:
        raise NetworkConfigError("acl_update must not be empty")
    return ConfigUpdateProposal(
        channel_id=config.channel_id,
        kind=ConfigUpdateKind.UPDATE_ACL,
        target_org_id="acl",
        proposer_admin_org=proposer_admin_org,
        acl_update=acl_update,
    )


def build_config_from_proposal(
    current: ChannelConfig,
    proposal: ConfigUpdateProposal,
) -> ChannelConfig:
    if proposal.channel_id != current.channel_id:
        raise NetworkConfigError("proposal channel_id mismatch")

    if proposal.kind is ConfigUpdateKind.ADD_ORG:
        if proposal.msp_definition is None:
            raise NetworkConfigError("add_org proposal requires msp_definition")
        member = ChannelMembership.from_msp_definition(proposal.msp_definition)
        membership = tuple(sorted(current.membership + (member,), key=lambda m: m.org_id))
        application = current.application
        capabilities = current.capabilities
    elif proposal.kind is ConfigUpdateKind.REMOVE_ORG:
        membership = tuple(
            member for member in current.membership if member.org_id != proposal.target_org_id
        )
        if len(membership) == len(current.membership):
            raise NetworkConfigError(f"organisation not on channel: {proposal.target_org_id}")
        application = current.application
        capabilities = current.capabilities
    elif proposal.kind is ConfigUpdateKind.ENABLE_CAPABILITY:
        capability = proposal.target_org_id
        membership = current.membership
        application = current.application
        if capability in current.capabilities.features:
            raise NetworkConfigError(f"capability already enabled: {capability!r}")
        capabilities = replace(
            current.capabilities,
            features=current.capabilities.features | {capability},
        )
    elif proposal.kind is ConfigUpdateKind.UPDATE_ACL:
        if proposal.acl_update is None:
            raise NetworkConfigError("update_acl proposal requires acl_update")
        membership = current.membership
        capabilities = current.capabilities
        application = replace(
            current.application,
            system_acl=merge_acl_rules(current.application.system_acl, proposal.acl_update),
        )
    else:
        raise NetworkConfigError(f"unsupported config update kind: {proposal.kind}")

    return replace(
        current,
        sequence=current.sequence + 1,
        membership=membership,
        application=application,
        capabilities=capabilities,
    )


def validate_modification_signatures(
    policy: ModificationPolicy,
    signatures: tuple[ConfigUpdateSignature, ...],
) -> None:
    signer_orgs = frozenset(item.admin_org for item in signatures)
    if not policy.satisfied_by(signer_orgs):
        required = policy.threshold
        raise NetworkConfigError(
            f"modification policy not satisfied: need {required} admin signatures, "
            f"got {len(signer_orgs)} from {sorted(signer_orgs)}"
        )


@dataclass
class ConfigUpdateWorkflow:
    """Policy-gated config update: propose → sign → order → commit → peer sync."""

    history: ChannelConfigHistory
    modification_policy: ModificationPolicy | None = None

    @property
    def policy(self) -> ModificationPolicy:
        if self.modification_policy is None:
            return default_modification_policy(self.history.current())
        return self.modification_policy

    def propose_add_org(self, msp_definition: OrgMSPDefinition, proposer: str) -> ConfigUpdateProposal:
        return propose_add_org(self.history.current(), msp_definition=msp_definition, proposer_admin_org=proposer)

    def propose_remove_org(self, org_id: str, proposer: str) -> ConfigUpdateProposal:
        return propose_remove_org(self.history.current(), org_id=org_id, proposer_admin_org=proposer)

    def propose_update_acl(
        self,
        acl_update: dict[str, frozenset[str]],
        proposer: str,
    ) -> ConfigUpdateProposal:
        return propose_update_acl(
            self.history.current(),
            acl_update=acl_update,
            proposer_admin_org=proposer,
        )

    def commit_proposal(
        self,
        proposal: ConfigUpdateProposal,
        signatures: tuple[ConfigUpdateSignature, ...],
    ) -> ChannelConfig:
        """Validate signatures, build next config, and append to channel history."""
        validate_modification_signatures(self.policy, signatures)
        if proposal.proposer_admin_org not in {item.admin_org for item in signatures}:
            raise NetworkConfigError("proposer admin org must sign the config update")
        next_config = build_config_from_proposal(self.history.current(), proposal)
        self.history.apply_update(next_config)
        return next_config


def greenledger_genesis_config(
    *,
    channel_id: str = "greenledger",
    protocol_version: str = "1.2.0",
) -> ChannelConfig:
    """Phase 1 default genesis config for the Greenledger channel."""
    return ChannelConfig(
        channel_id=channel_id,
        sequence=0,
        membership=(
            ChannelMembership(
                org_id="GreTelemetryOracle",
                msp_id="GreTelemetryOracleMSP",
                ca_root_certificate_pem="-----BEGIN CERTIFICATE-----\nORACLE-CA\n-----END CERTIFICATE-----",
            ),
            ChannelMembership(
                org_id="ZeegateOrg",
                msp_id="ZeegateOrgMSP",
                ca_root_certificate_pem="-----BEGIN CERTIFICATE-----\nZEEGATE-CA\n-----END CERTIFICATE-----",
            ),
            ChannelMembership(
                org_id="BytenergyOrg",
                msp_id="BytenergyOrgMSP",
                ca_root_certificate_pem="-----BEGIN CERTIFICATE-----\nBYTENERGY-CA\n-----END CERTIFICATE-----",
            ),
        ),
        ordering=OrderingParameters(
            orderer_count=1,
            max_block_size_bytes=512_000,
            batch_timeout_ms=2_000,
        ),
        application=ApplicationParameters(
            default_endorsement_policy=f"AND('{ORACLE_PEER_ID}')",
            access_control_list=frozenset({"tegalid_gate", "project_registry"}),
            system_acl=acl_pairs_from_rules(greenledger_system_acl_rules()),
        ),
        capabilities=ChannelCapabilities(
            protocol_version=protocol_version,
            features=frozenset({"gretelemetry_oracle"}),
        ),
    )


def new_config_history(genesis: ChannelConfig | None = None) -> ChannelConfigHistory:
    return ChannelConfigHistory(genesis=genesis or greenledger_genesis_config())
