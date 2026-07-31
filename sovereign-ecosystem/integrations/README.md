# Integrations

**Gretelemetry oracle** and dev producers. Tegalchain connects to external projects **only** through `mint_worker/` — not through subsystem code. See [docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md](../docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md).

| Path | Phase | Role |
|------|-------|------|
| `mint_worker/` | **1** (active) | **Oracle/adapter:** schema + tegalid gate + ZK verify → Tegalchain mint |
| `zeegate_telemetry/` | 1 | Dev producer simulating a telecom subsystem (independent of chain) |

Phase 2 voice lab (`zeegate-cloud/`) is a **Zeegate subsystem** concern — outside Tegalchain unless adapter-normalized CDR (with ZK on final public evidence) is posted via gretelemetry/Auditrail. See [GREETELEMETRY-ZK.md](../docs/contracts/GREETELEMETRY-ZK.md).
