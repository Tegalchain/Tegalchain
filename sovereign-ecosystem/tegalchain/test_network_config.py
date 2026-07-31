"""Tests for channel network configuration and update workflow."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.network_config import (  # noqa: E402
    ApplicationParameters,
    ChannelCapabilities,
    ChannelConfig,
    ChannelConfigHistory,
    ChannelMembership,
    ConfigUpdateSignature,
    ConfigUpdateWorkflow,
    ModificationPolicy,
    NetworkConfigError,
    OrderingParameters,
    OrgMSPDefinition,
    greenledger_genesis_config,
    new_config_history,
    propose_add_org,
)


class NetworkConfigTests(unittest.TestCase):
    def test_genesis_is_block_zero(self) -> None:
        genesis = greenledger_genesis_config()
        self.assertEqual(genesis.sequence, 0)
        self.assertIn("ZeegateOrg", genesis.org_ids())
        self.assertIn("GreTelemetryOracle", genesis.org_ids())

    def test_config_history_and_current(self) -> None:
        history = new_config_history()
        self.assertEqual(len(history.history()), 1)
        update = ChannelConfig(
            channel_id="greenledger",
            sequence=1,
            membership=(
                ChannelMembership(org_id="GreTelemetryOracle", msp_id="GreTelemetryOracleMSP"),
                ChannelMembership(org_id="ZeegateOrg", msp_id="ZeegateOrgMSP"),
                ChannelMembership(org_id="BytenergyOrg", msp_id="BytenergyOrgMSP"),
                ChannelMembership(org_id="FoundationOrg", msp_id="FoundationOrgMSP"),
            ),
            ordering=OrderingParameters(
                orderer_count=3,
                max_block_size_bytes=512_000,
                batch_timeout_ms=2_000,
            ),
            application=ApplicationParameters(
                default_endorsement_policy="AND('GreTelemetryOracle.peer')",
            ),
            capabilities=ChannelCapabilities(protocol_version="1.2.0"),
        )
        history.apply_update(update)
        self.assertEqual(history.current().sequence, 1)
        self.assertEqual(len(history.history()), 2)
        self.assertIn("FoundationOrg", history.current().org_ids())

    def test_rejects_bad_sequence(self) -> None:
        history = new_config_history()
        bad = ChannelConfig(
            channel_id="greenledger",
            sequence=3,
            membership=history.genesis.membership,
            ordering=history.genesis.ordering,
            application=history.genesis.application,
            capabilities=history.genesis.capabilities,
        )
        with self.assertRaises(NetworkConfigError):
            history.apply_update(bad)

    def test_assert_org_member(self) -> None:
        genesis = greenledger_genesis_config()
        genesis.assert_org_member("ZeegateOrg")
        with self.assertRaises(NetworkConfigError):
            genesis.assert_org_member("UnknownOrg")

    def test_add_org_workflow(self) -> None:
        history = new_config_history()
        workflow = ConfigUpdateWorkflow(
            history=history,
            modification_policy=ModificationPolicy(
                required_admin_orgs=frozenset({"GreTelemetryOracle", "ZeegateOrg", "BytenergyOrg"}),
                threshold=2,
            ),
        )
        foundation = OrgMSPDefinition(
            org_id="FoundationOrg",
            msp_id="FoundationOrgMSP",
            ca_root_certificate_pem="-----BEGIN CERTIFICATE-----\nFOUNDATION-CA\n-----END CERTIFICATE-----",
        )
        proposal = workflow.propose_add_org(foundation, proposer="ZeegateOrg")
        committed = workflow.commit_proposal(
            proposal,
            (
                ConfigUpdateSignature(admin_org="ZeegateOrg", signature="sig-z"),
                ConfigUpdateSignature(admin_org="BytenergyOrg", signature="sig-b"),
            ),
        )
        self.assertEqual(committed.sequence, 1)
        self.assertIn("FoundationOrg", committed.org_ids())
        member = committed.membership_index()["FoundationOrg"]
        self.assertIn("FOUNDATION-CA", member.ca_root_certificate_pem)

    def test_remove_org_workflow(self) -> None:
        history = new_config_history()
        workflow = ConfigUpdateWorkflow(
            history=history,
            modification_policy=ModificationPolicy(
                required_admin_orgs=frozenset({"GreTelemetryOracle", "ZeegateOrg", "BytenergyOrg"}),
                threshold=2,
            ),
        )
        proposal = workflow.propose_remove_org("BytenergyOrg", proposer="GreTelemetryOracle")
        committed = workflow.commit_proposal(
            proposal,
            (
                ConfigUpdateSignature(admin_org="GreTelemetryOracle", signature="sig-o"),
                ConfigUpdateSignature(admin_org="ZeegateOrg", signature="sig-z"),
            ),
        )
        self.assertNotIn("BytenergyOrg", committed.org_ids())
        self.assertIn("BytenergyOrg", history.removed_orgs)
        self.assertFalse(history.is_org_active("BytenergyOrg"))

    def test_add_org_requires_msp(self) -> None:
        genesis = greenledger_genesis_config()
        with self.assertRaises(NetworkConfigError):
            propose_add_org(
                genesis,
                msp_definition=OrgMSPDefinition("FoundationOrg", "FoundationOrgMSP", ""),
                proposer_admin_org="UnknownOrg",
            )


if __name__ == "__main__":
    unittest.main()
