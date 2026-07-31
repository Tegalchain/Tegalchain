# State access patterns

Canonical spec: [sovereign-ecosystem/docs/TEGALCHAIN.md#state-access-patterns](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/TEGALCHAIN.md#state-access-patterns).

Smart contracts use the **state API** on `ctx.state`:

| Operation | Description |
|-----------|-------------|
| `state.get(key)` | Read a single key |
| `state.put(key, value)` | Write a single key |
| `state.delete(key)` | Delete a key |
| `state.get_range(start, end)` | Range query over keys |
| `state.get_query(expression)` | Rich query (CouchDB only) |
| `state.get_history(key)` | Full history of a key's values |

`get_query` requires the CouchDB [state-database.md](./state-database.md) backend.

Phase 1 simulation: `tegalchain/state_access.py` (`ContractState`) in sovereign-ecosystem.

See also [contract-interface.md](./contract-interface.md) · [contract-best-practices.md](./contract-best-practices.md).
