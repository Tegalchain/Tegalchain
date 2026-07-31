# Access control lists

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#access-control-lists](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#access-control-lists).

ACLs define which identities may invoke **system functions**:

- Peer administration APIs  
- Event subscription APIs  
- Ledger query APIs  
- Config update proposal submission  

Stored in channel config (`system_acl`); updated via `UPDATE_ACL` config proposals.

Phase 1: `tegalchain/access_control.py` — `SystemFunction`, `assert_system_acl_allowed()`.

See also [network-configuration.md](./network-configuration.md).
