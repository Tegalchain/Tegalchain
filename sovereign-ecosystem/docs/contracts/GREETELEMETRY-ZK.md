# Gretelemetry ZK evidence on the Greenledger

**Status:** Contract + oracle hook (verification stub; production circuits on Tegalchain)  
**Protocol:** gretelemetry **v1.2.0** optional `zk_evidence`  
**Applies to:** Final telemetry and adapter-normalized evidence (including CDR) **committed to the Greenledger**

## Principle

Subsystems collect raw data internally (calls, meters, CDR rows). **Zero-Knowledge proofs attach only to the final public evidence** the gretelemetry oracle / Auditrail adapter sends to Tegalchain — not to subsystem internals.

```text
Raw data (private, stays in subsystem)
        │
        ▼
Adapter normalizes → public metrics / CDR summary (gretelemetry envelope)
        │
        ▼
ZK prover (witness = raw, public = final envelope fields)
        │
        ▼
Attach zk_evidence → HMAC sign → oracle verify → Auditrail / mint
        │
        ▼
Greenledger verifies ZK + tegalid + stores commitment (not raw CDR/telemetry)
```

Tegalchain never sees Zeegate/Bytenergy internals — only **public inputs + ZK proof + tegalid lock**.

## Evidence kinds

| `evidence_kind` | Source | Public fields on ledger |
|-----------------|--------|-------------------------|
| `GREETELEMETRY` | Mint oracle path | `system_type`, `metrics`, tegalid refs |
| `CDR` | Voice/data adapter | duration, byte counters, call id hash — not raw SIP |
| `AGGREGATE` | Periodic rollup adapter | window totals derived from verified child proofs |
| `ASSET_RETIREMENT` | PoREX / governance adapter | retirement amount, vintage, asset id |

All kinds use the same `zk_evidence` object shape in [schema.json](../../greentelemetry-protocol-spec/schema.json).

## `zk_evidence` object (v1.2)

| Field | Description |
|-------|-------------|
| `scheme` | Prover system, e.g. `groth16`, `placeholder-dev` (lab only) |
| `circuit_id` | Circuit version, e.g. `gretelemetry-v1`, `cdr-summary-v1` |
| `evidence_kind` | `GREETELEMETRY` \| `CDR` \| `AGGREGATE` \| `ASSET_RETIREMENT` |
| `public_inputs_hash` | `sha256` of canonical public inputs (hex) |
| `commitment` | Ledger-facing commitment to private witness (hex) |
| `proof` | Serialized proof bytes (hex) |

Public inputs for hashing are the gretelemetry envelope **excluding** `signature` and the entire `zk_evidence` block. The proof attests that private witness data (raw CDR, meters, etc.) is consistent with those public fields.

### Example (gretelemetry)

```json
{
  "node_id": "did:tegal:LABEDGE001",
  "project_id": "zeegate-telecom",
  "timestamp": 1750000000,
  "system_type": "ZEEGATE_TELECOM",
  "metrics": { "telecom_bandwidth_bytes": 8192 },
  "zk_evidence": {
    "scheme": "groth16",
    "circuit_id": "gretelemetry-v1",
    "evidence_kind": "GREETELEMETRY",
    "public_inputs_hash": "a1b2c3…",
    "commitment": "d4e5f6…",
    "proof": "070809…"
  },
  "signature": "hmac-sha256:…"
}
```

CDR records use the same `zk_evidence` block on the **adapter output** committed to Auditrail (not necessarily the gretelemetry HTTP envelope).

## Oracle verification order

```text
POST /v1/telemetry
  1. schema validate (incl. optional zk_evidence shape)
  2. tegalid gate
  3. HMAC verify
  4. ZK verify (TEGALCHAIN_ZK_MODE)
  5. mint + queue
```

| `TEGALCHAIN_ZK_MODE` | Behavior |
|----------------------|----------|
| `off` | Ignore `zk_evidence` (default for local dev) |
| `dev` | Accept missing ZK or `placeholder-dev`; validate hash binding if present |
| `required` | Require valid `zk_evidence`; reject `placeholder-dev` |

On-chain verification (future): Tegalchain `x/auditrail` / PoRE modules verify `proof` against `circuit_id` and registered verifying keys.

## Relationship to other contracts

- [GREETELEMETRY-ORACLE-BOUNDARY.md](./GREETELEMETRY-ORACLE-BOUNDARY.md) — subsystems independent; oracle only ingress
- [TEGALID-GREETELEMETRY.md](./TEGALID-GREETELEMETRY.md) — identity lock before mint
- `zeegate/blockchain/bridge/bridge.go` — legacy stub; production ZK prover lives in oracle/adapter layer or chain SDK

## Android / producer note

Producers may compute ZK at the edge or delegate to an **adapter** before Greenledger submission. The wire format to the oracle always includes the **final** public envelope + `zk_evidence`. Subsystem code must not send raw CDR or raw metering blobs to Tegalchain.

## Related

- [schema.json](../../greentelemetry-protocol-spec/schema.json)
- [tegalchain/zk_evidence.py](../../tegalchain/zk_evidence.py)
