"""Channel access control lists for system APIs.

See docs/TEGALCHAIN.md#access-control-lists.
"""

from __future__ import annotations

from enum import Enum


class AccessControlError(PermissionError):
    pass


class SystemFunction(str, Enum):
    PEER_ADMIN = "peer_admin"
    EVENT_SUBSCRIBE = "event_subscribe"
    LEDGER_QUERY = "ledger_query"
    CONFIG_UPDATE = "config_update"


def acl_pairs_from_rules(rules: dict[str, frozenset[str]]) -> frozenset[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for function, orgs in rules.items():
        for org in orgs:
            pairs.add((function, org))
    return frozenset(pairs)


def greenledger_system_acl_rules() -> dict[str, frozenset[str]]:
    admins = frozenset({"GreTelemetryOracle", "ZeegateOrg", "BytenergyOrg"})
    return {
        SystemFunction.PEER_ADMIN.value: admins,
        SystemFunction.EVENT_SUBSCRIBE.value: admins,
        SystemFunction.LEDGER_QUERY.value: admins,
        SystemFunction.CONFIG_UPDATE.value: admins,
    }


def assert_system_acl_allowed(
    system_acl: frozenset[tuple[str, str]],
    function: SystemFunction,
    caller_org: str,
) -> None:
    if (function.value, caller_org) not in system_acl:
        raise AccessControlError(
            f"ACL denied {function.value} for organisation {caller_org!r}"
        )


def merge_acl_rules(
    current: frozenset[tuple[str, str]],
    updates: dict[str, frozenset[str]],
) -> frozenset[tuple[str, str]]:
    index: dict[str, set[str]] = {}
    for function, org in current:
        index.setdefault(function, set()).add(org)
    for function, orgs in updates.items():
        index.setdefault(function, set()).update(orgs)
    pairs: set[tuple[str, str]] = set()
    for function, orgs in index.items():
        for org in orgs:
            pairs.add((function, org))
    return frozenset(pairs)
