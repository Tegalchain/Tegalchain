# Network configuration

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#network-configuration](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#network-configuration).

The **config block** captures channel operational parameters:

- **Membership** — channel organisations  
- **Ordering** — orderer count, block size limits, timeouts  
- **Application** — default endorsement policies, ACLs  
- **Capabilities** — enabled protocol features  

Every channel has a **genesis config block** (block 0) and a **history of configuration updates**.

Phase 1: `tegalchain/network_config.py` (`greenledger_genesis_config`, `ChannelConfigHistory`) in sovereign-ecosystem.

See also [endorsement-policies.md](./endorsement-policies.md) · [contract-lifecycle.md](./contract-lifecycle.md) · [gossip.md](./gossip.md).
