"""Tests for protocol modules aligned with docs/TEGALCHAIN.md."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tegalchain.block import is_block_candidate, merkle_root  # noqa: E402
from tegalchain.contract_interface import (  # noqa: E402
    ContractError,
    InMemoryContract,
    QueryRequest,
    StateView,
    TransactionContext,
    IdentityView,
    InvokeRequest,
)
from tegalchain.contract_lifecycle import (  # noqa: E402
    ContractDefinition,
    LifecyclePhase,
)
from tegalchain.contract_practices import (  # noqa: E402
    ContractValidationError,
    assert_create_if_absent,
    reject_external_oracle_fields,
    require_non_empty_string,
)
from tegalchain.endorsement import (  # noqa: E402
    assert_ready_for_ordering,
    attach_endorsements,
    Endorsement,
    ORACLE_PEER_ID,
)
from tegalchain.gossip import GossipFanout, GossipMessageType, publish_submitted_transaction  # noqa: E402
from tegalchain.protocol import NetworkPlane, TransactionPhase  # noqa: E402
from tegalchain.state import StateDatabaseBackend, StateLayer  # noqa: E402
from tegalchain.transaction import LedgerTransaction  # noqa: E402


class ProtocolModuleTests(unittest.TestCase):
    def test_transaction_phases_and_planes(self) -> None:
        self.assertEqual(TransactionPhase.ORDERING.value, "ordering")
        self.assertEqual(NetworkPlane.DATA.value, "data")

    def test_ledger_transaction_from_block_candidate(self) -> None:
        candidate = attach_endorsements(
            {
                "type": "TELEMETRY_MINT",
                "signer": "tegal1abc",
                "timestamp": 1700000000,
                "signature": "sig",
                "namespace": "gretelemetry",
                "mint_payload": {"node_id": "n1"},
                "state_key": "node:n1",
                "telemetry_hash": "abc",
            },
            [Endorsement(peer=ORACLE_PEER_ID)],
        )
        tx = LedgerTransaction.from_block_candidate(candidate)
        self.assertEqual(tx.sender, "tegal1abc")
        self.assertEqual(tx.payload["telemetry_hash"], "abc")

    def test_block_candidate_and_merkle_root(self) -> None:
        txs = [{"type": "TELEMETRY_MINT", "id": 1}, {"type": "TELEMETRY_MINT", "id": 2}]
        self.assertTrue(is_block_candidate(txs[0]))
        root_a = merkle_root(txs)
        root_b = merkle_root(txs)
        self.assertEqual(root_a, root_b)

    def test_contract_lifecycle_transitions(self) -> None:
        definition = ContractDefinition(
            name="asset",
            wasm_hash="hash",
            endorsement_policy_expr="AND('OrgA.peer')",
            required_orgs=frozenset({"OrgA"}),
        )
        installed = definition.with_phase(LifecyclePhase.INSTALL)
        approving = installed.with_phase(LifecyclePhase.APPROVE)
        with_org = approving.record_org_approval("OrgA")
        self.assertTrue(with_org.ready_to_commit())
        committed = with_org.with_phase(LifecyclePhase.COMMIT)
        active = committed.with_phase(LifecyclePhase.ACTIVE)
        self.assertEqual(active.phase, LifecyclePhase.ACTIVE)

    def test_asset_contract_interface_example(self) -> None:
        contract = InMemoryContract()

        def create_asset(ctx: TransactionContext, args: tuple[object, ...]) -> None:
            asset_id, owner, value = args
            require_non_empty_string(asset_id, "asset_id")
            assert_create_if_absent(ctx.state.exists, str(asset_id))
            ctx.state.put(
                str(asset_id),
                {"id": asset_id, "owner": owner, "value": value},
            )

        def transfer_asset(ctx: TransactionContext, args: tuple[object, ...]) -> None:
            asset_id, new_owner = args
            asset = ctx.state.get(str(asset_id))
            if not asset:
                raise ContractError(f"Asset {asset_id} not found")
            if asset["owner"] != ctx.identity.get_id():
                raise ContractError("Only the current owner can transfer this asset")
            asset = dict(asset)
            asset["owner"] = new_owner
            ctx.state.put(str(asset_id), asset)

        def get_asset(ctx: TransactionContext, args: tuple[object, ...]) -> object:
            return ctx.state.get(str(args[0]))

        contract.register_invoke("create_asset", create_asset)
        contract.register_invoke("transfer_asset", transfer_asset)
        contract.register_query("get_asset", get_asset)

        ctx = TransactionContext(
            state=StateView(),
            identity=IdentityView("owner1"),
            channel_id="greenledger",
            timestamp=1,
        )
        contract.invoke(
            ctx,
            InvokeRequest("asset", "create_asset", ("a1", "owner1", 100)),
        )
        self.assertEqual(
            contract.query(ctx, QueryRequest("asset", "get_asset", ("a1",))),
            {"id": "a1", "owner": "owner1", "value": 100},
        )
        contract.invoke(
            TransactionContext(
                state=ctx.state,
                identity=IdentityView("owner1"),
                channel_id="greenledger",
                timestamp=2,
            ),
            InvokeRequest("asset", "transfer_asset", ("a1", "owner2")),
        )

    def test_contract_practices_reject_oracle_fields(self) -> None:
        with self.assertRaises(ContractValidationError):
            reject_external_oracle_fields({"http_url": "https://example.com"})

    def test_state_database_backends(self) -> None:
        self.assertEqual(StateLayer.APPLICATION_OUTBOX.value, "application_outbox")
        self.assertEqual(StateDatabaseBackend.COUCHDB.value, "couchdb")

    def test_assert_ready_for_ordering(self) -> None:
        candidate = attach_endorsements(
            {"type": "TELEMETRY_MINT"},
            [Endorsement(peer=ORACLE_PEER_ID)],
        )
        assert_ready_for_ordering(candidate)
        with self.assertRaises(ValueError):
            assert_ready_for_ordering({"type": "TELEMETRY_MINT", "endorsements": []})

    def test_gossip_publish_after_submit(self) -> None:
        fanout = GossipFanout()
        candidate = attach_endorsements(
            {"type": "TELEMETRY_MINT", "signer": "addr", "timestamp": 1},
            [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash="h")],
        )
        message = publish_submitted_transaction(
            fanout,
            channel_id="greenledger",
            signer_peer="submitter.peer",
            block_number=1,
            block_candidate=candidate,
            submit_ref="chain-sig-123",
        )
        self.assertEqual(message.message_type, GossipMessageType.BLOCK_ANNOUNCEMENT)
        self.assertEqual(len(fanout.received), 1)


if __name__ == "__main__":
    unittest.main()
