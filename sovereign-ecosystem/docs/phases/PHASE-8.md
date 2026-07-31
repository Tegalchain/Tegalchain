# Phase 8 — TP-108 AI attestation (lab stub)

**Status:** **Complete** (lab stub) — verified 2026-07-30 (Replit)  
**Proof `gtr_id`:** `70206e10-205b-47f3-8e87-00e2914b115a` — Zeegate ingest + `CORROBORATION` **PASS** (`ratio=1.000`, 2 attestations)  
**Depends on:** [Phase 7](./PHASE-7.md) staging profile (tegalid + Bearer mint worker); [Phase 6](./PHASE-6.md) PoRE on ingest recommended  
**Goal:** Attach optional **`THIRD_PARTY`** AI/rule attestations to verified GTRs for fraud reduction — **not** custody, fabricated emissions, or sole mint gates  
**Stack:** [TP-108](../standards/TP-108-AI-ATTESTATION.md) · [TP-101](../standards/TP-101-GREENTELEMETRY.md) attestation metadata · optional future [TP-102](../standards/TP-102-PROOF-OF-RESONANCE.md) EQS input

Phase 8 is **optional** at the evidence layer. Producers MAY omit AI attestations entirely; Phase 7 flows remain valid without them.

## Scope

| Component | Location | Status |
|-----------|----------|--------|
| TP-108 standard (draft) | `docs/standards/TP-108-AI-ATTESTATION.md` | Done |
| `metadata.tp108` schema | `ai-attestation-spec/schema.json` | Done |
| Schema validator | `ai_attestation_spec/validate.py` | Done |
| Zeegate CDR ↔ bandwidth profile | `ai_attestation_spec/zeegate_corroboration.py` | Done — deterministic lab |
| Attestation builder | `ai_attestation_spec/attestation.py` | Done |
| Mint worker append route | `POST /v1/telemetry/records/{gtr_id}/attestations` | Done |
| Lab stub script | `scripts/phase8-ai-attest-stub.sh` | Done |
| Lab attester catalog | `tegalchain/data/ai_attesters.example.json` | Done |
| PoRE `AI_AUGMENTED` EQS modifiers | `proof_of_resonance_spec/` | **Open** |
| Live CDR corroboration (Phase 3 volume) | `zeegate-cloud/cdr_adapter/` | **Open** |
| Production attester registry + key rotation | tegalid / DAO | **Open** |

## Architecture

```text
Verified GTR (TP-101) + DEVICE attestation
        │
        ▼
Public inputs (CDR hash, bandwidth, binding) → inputs_hash
        │
        ▼
THIRD_PARTY attestation + metadata.tp108 (TP-108)
        │
        ├──► POST …/records/{gtr_id}/attestations (mint worker)
        ├──► GLE attestation_summary update (if archived)
        └──► (future) TP-102 optional EQS modifier under AI_AUGMENTED profile
```

**Reference profile:** `zeegate-cdr-bandwidth-v1` — edge bandwidth GTR corroborated against CDR `billsec` aggregate (no MSISDN on wire).

## Custodianless rules (normative)

AI attestations **MUST NOT**:

- Assert ownership or custody of edge assets
- Replace `DEVICE` / `OPERATOR` signatures on primary measurements
- Invent `value`, `unit`, or emissions not in producer-signed evidence
- Serve as the only mint or anchor gate

See [TP-108 § Custodianless and exclusion rules](../standards/TP-108-AI-ATTESTATION.md#custodianless-and-exclusion-rules).

---

## Run (Replit / WSL)

### Prerequisites

1. Phase 7 prod worker with Bearer (Shell 1 — leave running):

```bash
export MINT_WORKER_BEARER_TOKEN=$(openssl rand -hex 24)   # save echoed value
./scripts/restart-mint-worker-prod.sh
```

2. Shell 2 — **same token**:

```bash
export MINT_WORKER_BEARER_TOKEN=<paste-saved-hex-from-shell-1>
```

### Path A — ingest then corroborate (recommended)

```bash
./scripts/phase7-staging-ingest.sh
./scripts/phase8-ai-attest-stub.sh
```

Or with explicit `gtr_id`:

```bash
./scripts/phase8-ai-attest-stub.sh 70206e10-205b-47f3-8e87-00e2914b115a
```

### Path B — corroborate existing LABEDGE001 GTR

```bash
./scripts/phase8-ai-attest-stub.sh
# resolves latest did:tegal:LABEDGE001 from mint queue DB
```

### Expected stub output

```text
gtr_id=… verdict=PASS ratio=1.000
inputs_hash=…
"attestation_count": 2
"claim_type": "CORROBORATION"
"verdict": "PASS"
OK: Phase 8 AI corroboration attestation appended
```

Lab pairing: **1 MiB** edge bandwidth + **85s** CDR billsec from `zeegate-cloud/cdr_adapter/fixtures/sample_cdr.csv` → **PASS** band.

### Optional strict schema on append

```bash
export MINT_WORKER_VALIDATE_TP108=1
./scripts/restart-mint-worker-prod.sh   # Shell 1 — re-export token first
```

### Manual verify

```bash
curl -s -H "Authorization: Bearer $MINT_WORKER_BEARER_TOKEN" \
  "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | python3 -m json.tool | \
  grep -E '"attester_type"|claim_type|verdict|attestation_count|por_scores'
```

`/health` `features` should include `tp108_attestation_append` on mint worker **0.4.0+**.

---

## Exit criteria

### Lab stub (complete)

- [x] `./scripts/phase8-ai-attest-stub.sh` appends signed `THIRD_PARTY` attestation (`70206e10-205b-47f3-8e87-00e2914b115a`)
- [x] `metadata.tp108.claim_type` = `CORROBORATION`, `verdict` = `PASS`
- [x] Record shows **2** attestations (`DEVICE` + `THIRD_PARTY`)
- [x] `POST /v1/telemetry/records/{gtr_id}/attestations` live on staging worker
- [x] CI: `ai_attestation_spec` + `integrations.mint_worker.test_tp108_append`

### Production / stretch (open)

- [ ] Live CDR from [Phase 3](./PHASE-3.md) volume (not fixture-only)
- [ ] `ScoringProfile.AI_AUGMENTED` wired into PoRE EQS
- [ ] Production attester registry (non-lab Ed25519 keys)
- [ ] TP-108 standard promoted from **Draft** → **Live**
- [ ] Zeegate SaaS automated corroboration job (TP-107 control plane)

---

## Tests

```bash
python3 -m unittest discover -s ai_attestation_spec -p 'test_*.py' -v
python3 -m unittest integrations.mint_worker.test_tp108_append -v
```

---

## Related

- [TP-108-AI-ATTESTATION.md](../standards/TP-108-AI-ATTESTATION.md)
- [PHASE-7.md](./PHASE-7.md) — staging ingest prerequisite
- [ZEEGATE-DEPIN-CONTROL-PLANE.md](../platforms/ZEEGATE-DEPIN-CONTROL-PLANE.md)
- [scripts/phase8-ai-attest-stub.sh](../../scripts/phase8-ai-attest-stub.sh)
- [scripts/replit-sync-check.sh](../../scripts/replit-sync-check.sh) — verifies Phase 8 script present

## Next

- Close remaining [Phase 7](./PHASE-7.md) items (24h soak, optional tX* devnet)
- **TP-104 Transynths** — tX* mint gates using PoRE + evidence quality
- Extend TP-108 to live Zeegate CDR adapter pipeline

Track protocol maturity in [PROTOCOL-STACK.md](../PROTOCOL-STACK.md).
