# Greentelemetry Protocol Spec

**Standard:** **TP-101** GreenTelemetry — [docs/standards/TP-101-GREENTELEMETRY.md](../docs/standards/TP-101-GREENTELEMETRY.md)

Unified telemetry contract for **environmentally sustainable DePIN and utility projects**. Validated signed payloads are **GreenTelemetry Records (GTRs)**.

**Glossary:** `gretelemetry` = greentelemetry protocol; `GreTelemetry` = Zeegate Android client — see [docs/GLOSSARY.md](../docs/GLOSSARY.md).

**Oracle boundary:** Producers (Zeegate, Bytenergy, future nodes) are independent subsystems. Tegalchain sees only signed payloads accepted by the gretelemetry oracle — see [docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md](../docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md).

## Scope

All producers publish **`SovereignNodeTelemetry`** payloads validated by this schema. The **gretelemetry oracle** (`integrations/mint_worker`) is the sole ingress to Tegalchain mint/state — not direct subsystem integration.

| `system_type` | Project | Domain | Required metric(s) |
|---------------|---------|--------|-------------------|
| `ZEEGATE_TELECOM` | **Zerocell Zeegate** | DePIN telecom — gsm2sip, AnyFi WiFi backhaul, SIP/media | `telecom_bandwidth_bytes` |
| `BYTENERGY_UTILITY` | **Bytenergy Utility** | Prosumer / grid energy telemetry | `energy_generation_kwh` |
| *(future)* | Other sustainable nodes | Add via protocol minor bump — see below | Per-project metrics |

Examples of future `system_type` values (not yet in schema v1.0.0):

- Community mesh / climate sensors
- Water or soil monitoring nodes
- Additional Zerocell or partner DePIN verticals

## Version

See [VERSION](./VERSION) (currently **1.3.0**).

### v1.3.0 (canonical TP-101 GTR)

Root schema `oneOf`:

- **Canonical GTR v1** — `gtr_id`, `source_id`, `source_type`, `measurement_type`, `value`, `unit`, ISO `timestamp`, `attestations`, `schema_version: "1.0"`
- **Legacy SovereignNodeTelemetry** — normalized to GTR at the oracle ([TP-101-GREENTELEMETRY.md](../docs/standards/TP-101-GREENTELEMETRY.md))

Optional `location` (GeoPoint) on both shapes.

### v1.2.0 (ZK on final Greenledger evidence)

Optional `zk_evidence` — zero-knowledge proof over the **final public envelope** sent to the Greenledger (telemetry, adapter-normalized CDR, etc.). Private witness stays in the subsystem. See [docs/contracts/GREETELEMETRY-ZK.md](../docs/contracts/GREETELEMETRY-ZK.md).

### v1.1.0 (tegalid integration)

Optional fields for Tegalid project lock (see [docs/contracts/TEGALID-GREETELEMETRY.md](../docs/contracts/TEGALID-GREETELEMETRY.md)):

- `project_id` — Greenledger project slug
- `binding_id` — edge instance within project

v1.0 payloads without these fields remain valid.

## Adding a new sustainable project type

1. Bump **minor** in `VERSION` (backward compatible) or **major** if breaking.
2. Add enum value to `system_type` in [schema.json](./schema.json).
3. Add a `definitions/<project>_telemetry` block and include it in the root `oneOf`.
4. Update `greentelemetry_protocol_spec/models.py` and `tegalchain/mint.py` reward mapping.
5. Record compatibility in root [VERSIONS.json](../VERSIONS.json).

**Rule:** No ad-hoc JSON outside this schema — including Android, cloud, or chain adapters.

## Canonical file

- [schema.json](./schema.json) — JSON Schema draft-07, `additionalProperties: false`
