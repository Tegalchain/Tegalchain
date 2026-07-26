# Protocol upgrades

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#protocol-upgrades](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#protocol-upgrades).

Capabilities are **named flags** enabling protocol features after all nodes upgrade software.

1. All nodes upgrade  
2. Admins verify node versions  
3. Capabilities update proposed via config process  
4. Capability activates  

Phase 1: `tegalchain/capabilities.py` — `CapabilityUpgradeWorkflow`, `ENABLE_CAPABILITY` config updates.

See also [network-configuration.md](./network-configuration.md).
