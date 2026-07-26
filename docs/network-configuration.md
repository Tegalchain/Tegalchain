# Network configuration

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#network-configuration](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#network-configuration).

The **config block** captures channel operational parameters:

- **Membership** — channel organisations  
- **Ordering** — orderer count, block size limits, timeouts  
- **Application** — default endorsement policies, ACLs  
- **Capabilities** — enabled protocol features  

Every channel has a **genesis config block** (block 0) and a **history of configuration updates**.

## Configuration update process

1. Admin generates a **config update proposal**  
2. Administrators **collect signatures**  
3. Satisfied **modification policy** → submit to ordering service  
4. Ordering service **commits** config update as special transaction  
5. All peers **update local configuration**

## Membership management

**Add org:** new org supplies CA root + MSP → admin proposal → member approvals → peers join after commit.

**Remove org:** same workflow removes MSP; certs invalid for new txs; historical ledger records intact.

Phase 1: `tegalchain/network_config.py` — `ConfigUpdateWorkflow`, `OrgMSPDefinition`, `ModificationPolicy`.

See also [endorsement-policies.md](./endorsement-policies.md) · [contract-lifecycle.md](./contract-lifecycle.md) · [gossip.md](./gossip.md) · [protocol-upgrades.md](./protocol-upgrades.md) · [access-control-lists.md](./access-control-lists.md).
