# Tegalid ↔ Greentelemetry ↔ Mint contract

**Status:** Implemented (bridge + mint worker)  
**Protocol:** greentelemetry **v1.1.0** (optional `project_id`, `binding_id`)  
**Chain modules:** `x/tegalid` (identity lock), `x/auditrail` (verified evidence)  
**Scope:** Any registered environmentally sustainable DePIN or utility project on the Greenledger.

**Boundary:** Tegalchain does **not** integrate with Zeegate, Bytenergy, or other subsystems directly. The **only** link is the gretelemetry oracle/adapter — see [GREETELEMETRY-ORACLE-BOUNDARY.md](./GREETELEMETRY-ORACLE-BOUNDARY.md).

## Purpose

Define how **Tegalid** on the Tegalchain Greenledger gates **gretelemetry** ingestion at the Phase 1 mint worker for any registered sustainable project, and how evidence flows to **Auditrail**.

| Layer | Responsibility |
|-------|----------------|
| **Tegalid** | DID, KYC, attestation, **project lock** (any Greenledger project), P2P control messaging |
| **Greenledger project registry** | Which `project_id` values are active, their `system_type`, sustainability category |
| **gretelemetry** | Signed measurement envelope (`schema.json`) — extensible `system_type` per project vertical |
| **Mint worker (gretelemetry oracle)** | Schema + tegalid gate + project registry + HMAC + mint queue |
| **Auditrail** | Durable verified gretelemetry, adapter-normalized CDR, asset retirement |
| **External producers** | Independent subsystems; publish signed telemetry only |

### Current vs future projects

| project_id | system_type | Category | Status |
|------------|-------------|----------|--------|
| `zeegate-telecom` | `ZEEGATE_TELECOM` | DePIN telecom vertical | active |
| `bytenergy-utility` | `BYTENERGY_UTILITY` | Utility energy vertical | active |
| *(future)* | *(schema bump)* | Other sustainable verticals | planned |

Project names are registry identifiers only. Tegalchain never depends on subsystem implementation details.

Register new verticals in [tegalchain/data/greenledger_projects.json](../../tegalchain/data/greenledger_projects.json), bump gretelemetry schema minor when adding `system_type`, then issue tegalid `NodeBinding` on-chain.

## Identity rule

`node_id` in every telemetry payload **must** be a Tegalid DID in tegalid mode:

```text
did:tegal:<greenledger_address>
```

Example: `did:tegal:QORTALSTYLEADDRESS123`

In **dev mode** (`TEGALCHAIN_IDENTITY_MODE=dev`), legacy free-form `node_id` strings remain allowed for local testing with the shared dev HMAC key.

## NodeBinding (on-chain target)

Tegalid stores a **NodeBinding** per edge instance. Mint eligibility is derived on-chain; the mint worker reads bindings via cache file or REST (future).

| Field | Type | Description |
|-------|------|-------------|
| `did` | string | Tegalid DID (= gretelemetry `node_id`) |
| `project_id` | string | Greenledger project slug — **must** exist in project registry |
| `system_type` | enum | gretelemetry `system_type` for this project vertical |
| `binding_id` | string | Edge instance id (SIM slot, device hash) |
| `kyc_level` | enum | `NONE` \| `BASIC` \| `VERIFIED` |
| `attestation_score` | int | Aggregated from `attest-did` |
| `status` | enum | `PENDING` \| `ACTIVE` \| `SUSPENDED` \| `REVOKED` |
| `mint_eligible` | bool | Keeper-derived gate for rewards |
| `tegal_address` | string | On-chain reward address |
| `telemetry_key_id` | string | HMAC key identifier |
| `telemetry_hmac_secret` | bytes | **Off-chain only** — never committed to chain |
| `sip_user` | string | Optional — Kamailio username (telecom/DePIN voice projects only) |
| `sip_domain` | string | Optional — SIP domain when `requires_sip` on project |
| `sip_credential_commitment` | hex | `sha256(user:domain:secret)` |
| `metadata_uri` | string | IPFS / registry URI |
| `expires_at` | int | Unix seconds; `0` = no expiry |

### Mint eligibility (keeper logic)

```text
mint_eligible =
  status == ACTIVE
  AND kyc_level >= project.min_kyc
  AND attestation_score >= project.min_attestation
  AND project_id registered as **active** in Greenledger project registry
  AND binding.system_type matches registry entry for project_id
  AND (expires_at == 0 OR now < expires_at)
```

## Gretelemetry v1.1 envelope

Required (unchanged from v1.0): `node_id`, `timestamp`, `system_type`, `metrics`, `signature`.

Optional (v1.1):

| Field | Rule |
|-------|------|
| `project_id` | If present, must match binding `project_id` |
| `binding_id` | If present, must match binding `binding_id` |

Example (`ZEEGATE_TELECOM` / `zeegate-telecom`):

```json
{
  "node_id": "did:tegal:LABEDGE001",
  "project_id": "zeegate-telecom",
  "binding_id": "edge-sim-01",
  "timestamp": 1750000000,
  "system_type": "ZEEGATE_TELECOM",
  "metrics": { "telecom_bandwidth_bytes": 8192 },
  "signature": "hmac-sha256:…"
}
```

Example (`BYTENERGY_UTILITY` / `bytenergy-utility`):

```json
{
  "node_id": "did:tegal:LABENERGY01",
  "project_id": "bytenergy-utility",
  "binding_id": "meter-main",
  "timestamp": 1750000000,
  "system_type": "BYTENERGY_UTILITY",
  "metrics": { "energy_generation_kwh": 12.5 },
  "signature": "hmac-sha256:…"
}
```

HMAC is computed over canonical JSON **excluding** `signature` (same as v1.0). Optional fields participate in signing when present.

## Mint worker gate sequence

```text
POST /v1/telemetry
  1. validate_telemetry()          → JSON Schema v1.1
  2. tegalid_gate (if mode=tegalid)
       - node_id is did:tegal:…
       - binding exists for did + system_type
       - project_id registered (Greenledger) and matches system_type
       - binding.mint_eligible
       - project_id / binding_id match if provided
  3. verify_telemetry_signature()  → per-binding HMAC secret
  4. verify_zk_evidence()          → ZK on final public envelope (see GREETELEMETRY-ZK.md)
  5. mint_from_telemetry()         → tegal_address from binding
  6. enqueue mint queue
```

### HTTP status codes

| Code | Condition |
|------|-----------|
| 401 | Invalid HMAC |
| 403 | Not tegalid-locked, not mint eligible, suspended, project mismatch |
| 422 | Schema violation |
| 409 | Duplicate telemetry hash (future Auditrail dedupe) |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEGALCHAIN_IDENTITY_MODE` | `dev` | `dev` \| `tegalid` |
| `TEGALID_BINDINGS_FILE` | `tegalchain/data/tegalid_bindings.json` | Local binding cache (lab / until REST query) |
| `TEGALID_PROJECTS_FILE` | `tegalchain/data/greenledger_projects.json` | Active sustainable / utility project registry |
| `TEGALID_API_URL` | *(unset)* | Future: Cosmos query base URL |

Lab: copy `tegalchain/data/tegalid_bindings.example.json` → `tegalid_bindings.json`.

## Optional: telecom SIP (outside Tegalchain)

Some DePIN telecom **producers** use SIP infrastructure in their own subsystem. That is provisioned off-chain after tegalid binding. Tegalchain and the gretelemetry oracle do not configure or observe SIP — only signed telemetry and Auditrail evidence matter on the ledger.

## Auditrail evidence flow

Auditrail is append-only verified evidence on the Greenledger:

| `record_type` | Source | Key fields |
|---------------|--------|------------|
| `GREETELEMETRY` | Mint worker accept | `did`, `project_id`, `telemetry_hash`, `zk_evidence`, metrics snapshot |
| `CDR` | Adapter (final public summary + ZK) | Verified record — not raw subsystem CDR |
| `ASSET_RETIREMENT` | PoREX / governance | asset id, vintage, retired amount |

```text
Producer (any subsystem) → gretelemetry oracle → mint queue → chain
                                              ↘ Auditrail GREETELEMETRY
Adapter-normalized evidence → Auditrail (CDR, retirement, …)
```

Mint worker `block_candidate` includes `tegalid_did`, `project_id`, and `binding_id` when bound for Auditrail correlation.

## Tegalid P2P messaging

Use tegalid `send-message` for **control plane** only (credential rotation, suspension notice). Do not route bulk telemetry or CDR over P2P messaging.

## Related files

- [GREETELEMETRY-ZK.md](./GREETELEMETRY-ZK.md)
- [GREETELEMETRY-ORACLE-BOUNDARY.md](./GREETELEMETRY-ORACLE-BOUNDARY.md)
- [greentelemetry-protocol-spec/schema.json](../../greentelemetry-protocol-spec/schema.json)
- [tegalchain/tegalid_gate.py](../../tegalchain/tegalid_gate.py)
- [tegalchain/data/greenledger_projects.json](../../tegalchain/data/greenledger_projects.json)
- [tegalchain/project_registry.py](../../tegalchain/project_registry.py)
- [tegalchain/data/tegalid_bindings.example.json](../../tegalchain/data/tegalid_bindings.example.json)
- [integrations/mint_worker/server.py](../../integrations/mint_worker/server.py)
