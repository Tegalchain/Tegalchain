"""Tests for endorsement policy evaluation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.endorsement import (  # noqa: E402
    AND,
    OR,
    OutOf,
    DEFAULT_GREETELEMETRY_POLICY,
    Endorsement,
    ORACLE_PEER_ID,
    attach_endorsements,
    endorsements_satisfy_policy,
)


class EndorsementPolicyTests(unittest.TestCase):
    def test_and_requires_all_peers(self) -> None:
        policy = AND("OrgA.peer", "OrgB.peer")
        none = endorsements_satisfy_policy(policy, [])
        one = endorsements_satisfy_policy(
            policy, [Endorsement(peer="OrgA.peer")]
        )
        both = endorsements_satisfy_policy(
            policy,
            [Endorsement(peer="OrgA.peer"), Endorsement(peer="OrgB.peer")],
        )
        self.assertFalse(none)
        self.assertFalse(one)
        self.assertTrue(both)

    def test_or_requires_any_peer(self) -> None:
        policy = OR("OrgA.peer", "OrgB.peer")
        self.assertFalse(endorsements_satisfy_policy(policy, []))
        self.assertTrue(
            endorsements_satisfy_policy(policy, [Endorsement(peer="OrgB.peer")])
        )

    def test_out_of_threshold(self) -> None:
        policy = OutOf(2, "OrgA.peer", "OrgB.peer", "OrgC.peer")
        self.assertFalse(endorsements_satisfy_policy(policy, []))
        self.assertFalse(
            endorsements_satisfy_policy(policy, [Endorsement(peer="OrgA.peer")])
        )
        self.assertTrue(
            endorsements_satisfy_policy(
                policy,
                [Endorsement(peer="OrgA.peer"), Endorsement(peer="OrgC.peer")],
            )
        )

    def test_default_gretelemetry_policy(self) -> None:
        self.assertFalse(endorsements_satisfy_policy(DEFAULT_GREETELEMETRY_POLICY, []))
        self.assertTrue(
            endorsements_satisfy_policy(
                DEFAULT_GREETELEMETRY_POLICY,
                [Endorsement(peer=ORACLE_PEER_ID)],
            )
        )

    def test_attach_endorsements(self) -> None:
        candidate = {"type": "TELEMETRY_MINT", "signer": "addr"}
        enriched = attach_endorsements(
            candidate,
            [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="abc")],
        )
        self.assertEqual(enriched["type"], "TELEMETRY_MINT")
        self.assertEqual(len(enriched["endorsements"]), 1)
        self.assertEqual(enriched["endorsements"][0]["peer"], ORACLE_PEER_ID)
        self.assertEqual(enriched["endorsements"][0]["read_write_set_hash"], "abc")


if __name__ == "__main__":
    unittest.main()
