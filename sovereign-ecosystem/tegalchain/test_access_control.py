"""Tests for channel access control lists."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.access_control import (  # noqa: E402
    AccessControlError,
    SystemFunction,
    assert_system_acl_allowed,
    greenledger_system_acl_rules,
)
from tegalchain.network_config import (  # noqa: E402
    ConfigUpdateSignature,
    ConfigUpdateWorkflow,
    ModificationPolicy,
    greenledger_genesis_config,
    new_config_history,
)


class AccessControlTests(unittest.TestCase):
    def test_greenledger_acl_allows_admin_config_update(self) -> None:
        genesis = greenledger_genesis_config()
        assert_system_acl_allowed(
            genesis.application.system_acl,
            SystemFunction.CONFIG_UPDATE,
            "ZeegateOrg",
        )

    def test_acl_denies_unknown_org(self) -> None:
        genesis = greenledger_genesis_config()
        with self.assertRaises(AccessControlError):
            assert_system_acl_allowed(
                genesis.application.system_acl,
                SystemFunction.LEDGER_QUERY,
                "UnknownOrg",
            )

    def test_update_acl_via_config_workflow(self) -> None:
        history = new_config_history()
        workflow = ConfigUpdateWorkflow(
            history=history,
            modification_policy=ModificationPolicy(
                required_admin_orgs=frozenset({"GreTelemetryOracle", "ZeegateOrg", "BytenergyOrg"}),
                threshold=2,
            ),
        )
        proposal = workflow.propose_update_acl(
            {SystemFunction.LEDGER_QUERY.value: frozenset({"FoundationOrg"})},
            proposer="GreTelemetryOracle",
        )
        committed = workflow.commit_proposal(
            proposal,
            (
                ConfigUpdateSignature(admin_org="GreTelemetryOracle", signature="sig-o"),
                ConfigUpdateSignature(admin_org="ZeegateOrg", signature="sig-z"),
            ),
        )
        assert_system_acl_allowed(
            committed.application.system_acl,
            SystemFunction.LEDGER_QUERY,
            "FoundationOrg",
        )


if __name__ == "__main__":
    unittest.main()
