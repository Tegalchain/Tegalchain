# Zeegate DePIN — SaaS control plane

**Layer:** TP-107 Sovereign Platform  
**Vertical:** `zeegate-telecom` · `ZEEGATE_TELECOM`  
**Related:** [TEGALID-GREETELEMETRY.md](../contracts/TEGALID-GREETELEMETRY.md) · [TP-103 custodianless](../standards/TP-103-GREENLEDGER.md#custodianless-by-design)

Zeegate DePIN is the **SaaS control plane** for telecom edge capacity. It is **not** a GreenLedger storage node and **does not** take custody of participant assets. It registers **attested edge identities** that publish evidence to **Tegalchain**; provenance is archived on **GreenLedger (TP-103)** after oracle verification.

## Roles

| Piece | Role |
|-------|------|
| **Zeegate DePIN (SaaS)** | Fleet onboarding, bindings, voice stack (`zeegate-cloud`), Android edge (`zeegate/`) |
| **Edge / zerocell** | Sovereign producer — operational custody stays with the asset owner |
| **Tegalchain** | Permissioned ledger: **tegalid** identity lock, anchor txs, future tX* / governance |
| **GreenLedger (TP-103)** | Provenance archive: GLE, Auditrail, Carbon Account views |
| **Gretelemetry oracle** | Mint worker — sole ingress; subsystems never talk to the ledger directly |

**Correct framing:** edges become **tegalid-verified producers on Tegalchain**; anchored GTRs become **GLE records on GreenLedger**. Zeegate does not “join GreenLedger as a node.”

## Attested keys (256-bit class)

| Mechanism | Purpose |
|-----------|---------|
| **HMAC-SHA256** | Legacy/staging producer signing over canonical telemetry |
| **Ed25519** | TP-101 GTR attestations (256-bit-curve class) over canonical GTR hash |
| **Tegalid `NodeBinding`** | DID (`did:tegal:…`), `project_id`, `binding_id`, KYC/attestation score, off-chain telemetry HMAC secret |
| **Oracle gate** | Mint worker verifies signature + binding + project registry before mint eligibility |

Higher binding attestation flows into **TP-102 PoRE** (`eqs`, `resonance_score`). Optional **TP-108** CDR ↔ bandwidth corroboration may attach as `THIRD_PARTY` attestations — see [TP-108-AI-ATTESTATION.md](../standards/TP-108-AI-ATTESTATION.md).

## Evidence flow (custodianless)

```text
Zeegate SaaS control plane
  │  NodeBinding + attested keys
  ▼
Edge DePIN node (custody retained)
  │  signed gretelemetry (TP-101 GTR)
  ▼
Gretelemetry oracle
  │  tegalid gate + TP-102 PoRE
  ▼
Tegalchain anchor (ledger_ref)
  ▼
GreenLedger GLE + Auditrail + Carbon Account
  ▼
(future) eligible provenance → tX* (TP-104) → DAO collateral (TP-105/106)
```

## Implementation in this repo

| Component | Path |
|-----------|------|
| Android edge | `zeegate/` |
| Voice / CDR lab | `zeegate-cloud/` |
| Python producer sim | `integrations/zeegate_telemetry/` |
| Tegalid bindings (lab) | `tegalchain/data/tegalid_bindings.example.json` |
| Project registry | `tegalchain/data/greenledger_projects.json` |

P2P tegalid messaging is **control plane only** (rotation, suspension) — not bulk telemetry. See [TEGALID-GREETELEMETRY.md](../contracts/TEGALID-GREETELEMETRY.md).
