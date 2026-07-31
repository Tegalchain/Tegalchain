"""Tests for protocol capabilities and upgrade workflow."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.capabilities import (  # noqa: E402
    CapabilityUpgradeError,
    CapabilityUpgradeWorkflow,
    NodeVersionReport,
    capability_is_active,
    verify_all_nodes_support_capability,
)
from tegalchain.network_config import (  # noqa: E402
    ConfigUpdateSignature,
    ConfigUpdateWorkflow,
    ModificationPolicy,
    new_config_history,
)


class CapabilityUpgradeTests(unittest.TestCase):
    def setUp(self) -> None:
        history = new_config_history()
        self.workflow = CapabilityUpgradeWorkflow(
            config_workflow=ConfigUpdateWorkflow(
                history=history,
                modification_policy=ModificationPolicy(
                    required_admin_orgs=frozenset(
                        {"GreTelemetryOracle", "ZeegateOrg", "BytenergyOrg"}
                    ),
                    threshold=2,
                ),
            ),
            node_reports=(
                NodeVersionReport("peer-1", "1.2.0", frozenset({"zk_evidence_optional"})),
                NodeVersionReport("peer-2", "1.2.0", frozenset({"zk_evidence_optional"})),
            ),
        )

    def test_verify_nodes_support_capability(self) -> None:
        verify_all_nodes_support_capability(
            "zk_evidence_optional",
            self.workflow.node_reports,
        )
        with self.assertRaises(CapabilityUpgradeError):
            verify_all_nodes_support_capability(
                "multi_org_endorsement",
                self.workflow.node_reports,
            )

    def test_enable_capability_via_config_update(self) -> None:
        self.assertFalse(
            capability_is_active(
                self.workflow.config_workflow.history.current(),
                "zk_evidence_optional",
            )
        )
        committed = self.workflow.commit_enable(
            "zk_evidence_optional",
            proposer="ZeegateOrg",
            signatures=(
                ConfigUpdateSignature(admin_org="ZeegateOrg", signature="sig-z"),
                ConfigUpdateSignature(admin_org="BytenergyOrg", signature="sig-b"),
            ),
        )
        self.assertTrue(capability_is_active(committed, "zk_evidence_optional"))


if __name__ == "__main__":
    unittest.main()
