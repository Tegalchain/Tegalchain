# Gretelemetry oracle boundary

**Rule:** Tegalchain connects to external projects **only** through the **gretelemetry oracle/adapter** (mint worker ingress → tegalid gate → mint queue → chain). It has **no dependency on, and no interest in**, what happens inside Zeegate, Bytenergy, or any other subsystem.

## Independent subsystems

```text
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Zeegate         │     │ Bytenergy       │     │ Future nodes    │
│ (Android DePIN) │     │ (utility client)│     │ (independent)   │
│ internal: SIP,  │     │ internal: meters│     │ internal: *     │
│ AnyFi, PJSIP…   │     │ inverters…      │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │    ONLY interface: signed greentelemetry (+ optional ZK on final evidence)
         └───────────────────────┼───────────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │ greentelemetry oracle / adapter       │
              │ integrations/mint_worker              │
              │  · schema validate (schema.json)      │
              │  · tegalid identity + project lock    │
              │  · HMAC verify                        │
              │  · ZK evidence verify (final payload) │
              │  · mint candidate + queue             │
              └──────────────────┬───────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │ Tegalchain Greenledger                │
              │  · verify ZK proof on-chain (future)  │
              │  · x/tegalid · x/auditrail · mint     │
              └──────────────────────────────────────┘
```

`*` Tegalchain never imports, configures, or branches on subsystem internals (voice stack, Android services, utility hardware, etc.).

## What crosses the boundary

| Allowed on the wire | Not Tegalchain's concern |
|---------------------|---------------------------|
| `SovereignNodeTelemetry` per [schema.json](../../greentelemetry-protocol-spec/schema.json) | How metrics were collected |
| Tegalid DID (`node_id`), optional `project_id` / `binding_id` | Edge app architecture |
| HMAC `signature` | Raw CDR rows, SIP, subsystem logs |
| Optional `zk_evidence` on **final** public envelope | ZK private witness (proven off-ledger) |
| `system_type` + required `metrics` fields | |

## Oracle responsibilities

The mint worker is the **canonical gretelemetry oracle** at the ecosystem edge:

1. Reject payloads that deviate from `schema.json`
2. Enforce tegalid mint eligibility ([TEGALID-GREETELEMETRY.md](./TEGALID-GREETELEMETRY.md))
3. Verify producer HMAC (per-binding in production)
4. Verify ZK evidence on final public payload ([GREETELEMETRY-ZK.md](./GREETELEMETRY-ZK.md))
5. Emit chain-neutral `TELEMETRY_MINT` block candidates
6. Enqueue for submitter / Auditrail correlation

Subsystem producers (Python stubs, Android `TelemetryService`, future adapters) are **replaceable**. Tegalchain logic must not name or import Zeegate/Bytenergy modules.

## Auditrail

Verified gretelemetry (with ZK) and adapter-normalized CDR/retirement records are committed to **Auditrail** — ZK applies to the final evidence, not raw subsystem exports.

## Adding a project

1. Register `project_id` in [greenledger_projects.json](../../tegalchain/data/greenledger_projects.json)
2. Add `system_type` + metrics to greentelemetry schema (minor bump)
3. Ship a **producer** in that subsystem + optional **adapter** if evidence needs normalization (CDR, etc.) with ZK on final public output
4. Issue tegalid `NodeBinding` on-chain

No changes to Tegalchain core beyond tegalid/Auditrail/mint policy for that `system_type`'s metrics shape.

## Related

- [GREETELEMETRY-ZK.md](./GREETELEMETRY-ZK.md) — ZK on final Greenledger evidence
- [TEGALID-GREETELEMETRY.md](./TEGALID-GREETELEMETRY.md) — identity lock + mint gate
- [greentelemetry-protocol-spec/README.md](../../greentelemetry-protocol-spec/README.md) — protocol scope
