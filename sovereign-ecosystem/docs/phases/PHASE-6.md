# Phase 6 — TP-102 Proof of Resonance

**Status:** **Complete** (lab) — verified 2026-07-28  
**Proof `gtr_id`:** `5d8528c0-ce18-4a13-9be9-59fedb095049` — `por_scores` TP-102 valid (`eqs` 0.45, `riv` 104857.6, `resonance_score` 72)
**Depends on:** Phase 1 oracle (TP-101 GTR); Phases 3–5 recommended (scored evidence paths proven)  
**Goal:** Attach **PoRE (RFM)** scores to verified GTRs and expose them on the record API — input to future PoREF / PoREX and [TP-104](../PROTOCOL-STACK.md#tp-104--transynth-standard) tX* gates  
**Stack:** [TP-102](../standards/TP-102-PROOF-OF-RESONANCE.md) · [proof-of-resonance-spec/](../../proof-of-resonance-spec/)

Only GTRs that passed TP-101 verification enter TP-102. Raw CDR CSV and Android internals never cross this boundary.

## Scope

| Component | Location | Status |
|-----------|----------|--------|
| TP-102 standard doc | `docs/standards/TP-102-PROOF-OF-RESONANCE.md` | Done |
| PoR JSON schema | `proof-of-resonance-spec/schema.json` | Done |
| RFM scoring | `tegalchain/por/score_gtr.py` | Done — wired at ingest |
| `block_candidate.tp102_rfm` | `tegalchain/gtr.py` | Done |
| GET `por_scores` | `integrations/mint_worker/ingest.py` | Done |
| Lab verify script | `scripts/phase6-verify-por.sh` | Done |
| PoREF validator consensus | `tegalchain-core` Cosmos | Target |
| PoREX / tX* mint gates | TP-104 contracts | Target |

## Architecture

```text
Verified GTR (TP-101 oracle)
        │
        ▼
tegalchain/por — EQS, RIV, resonance_score (RFM)
        │
        ▼
block_candidate.tp102_rfm  +  GET por_scores
        │
        ├──► TP-103 GLE archival (unchanged)
        └──► TP-104 tX* eligibility (future)
```

## Lab scoring reference (phase1_oracle profile)

| Evidence | Typical `eqs` | `riv` driver | Notes |
|----------|---------------|--------------|-------|
| Zeegate `telecom_bandwidth_bytes` ~1 MiB | ~0.45 | `value × 0.1` | `SourceType.API`, dev attestation |
| Bytenergy `energy_generation_kwh` ~3.42 | ~0.45 | `value × 0.05` | `MeasurementType.ENERGY_KWH` |
| CDR `bytes` > 0 | ~0.45 | higher with byte counters | `evidence_kind: CDR` in metadata |
| CDR loopback 0 bytes | ~0.45 | 0.0 | Still scores; lower `resonance_score` |

All lab RFM payloads validate against `proof-of-resonance-spec/schema.json`.

---

## Run (Replit / WSL)

### Shell 1 — mint worker

After `git pull`, **restart** the worker so GET `/records` exposes `por_scores` (a stale process keeps old code):

```bash
cd ~/workspace/sovereign-ecosystem
git pull origin main
./scripts/restart-mint-worker.sh
```

Or first start: `./scripts/start-mint-worker.sh`

### Shell 2 — verify PoR on new ingest

```bash
cd ~/workspace/sovereign-ecosystem
git pull origin main
chmod +x scripts/phase6-verify-por.sh
./scripts/phase6-verify-por.sh ingest
```

Expected output includes:

```
protocol_standard: TP-102
eqs: 0.45
resonance_score: …
OK: TP-102 schema valid
```

### Verify an existing GTR (Phase 4/5 records)

Records ingested after TP-102 wiring store `tp102_rfm` in the queue row:

```bash
./scripts/phase6-verify-por.sh verify 5ed46400-89be-4d65-91e8-2a809b1f1b15
./scripts/phase6-verify-por.sh verify 810947b8-bd63-4864-bb59-337d10514905
```

Manual check:

```bash
curl -s "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | python3 -m json.tool | \
  grep -E '"por_scores"|"eqs"|"riv"|"resonance_score"|protocol_standard'
```

---

## Exit criteria

- [x] `./scripts/phase6-verify-por.sh verify <gtr_id>` → `OK: TP-102 schema valid` (`5d8528c0-ce18-4a13-9be9-59fedb095049`)
- [x] `GET /v1/telemetry/records/{gtr_id}` includes `por_scores` with `protocol_standard: TP-102`
- [ ] CDR and edge GTRs both score (compare Phase 3 vs Phase 4 `gtr_id`s) — optional stretch; edge Zeegate proved
- [x] `score_gtr_for_por()` invoked on every ingest (`tegalchain/gtr.py`)
- [x] CI: `tegalchain/test_por.py` + `proof_of_resonance_spec` tests
- [ ] (Stretch) Validator Resonance eligibility hook for devnet

## Tests

```bash
python3 -m unittest tegalchain.test_por tegalchain.test_gtr -v
python3 -m unittest discover -s proof_of_resonance_spec -p 'test_*.py' -v
python3 -m unittest integrations.mint_worker.test_server -v
```

## Related

- [TP-102-PROOF-OF-RESONANCE.md](../standards/TP-102-PROOF-OF-RESONANCE.md)
- [PHASE-5.md](./PHASE-5.md) — cosmos anchor (complete lab)
- [tegalchain-core/docs/proof-of-resonance-stack.md](../../tegalchain-core/docs/proof-of-resonance-stack.md)
- [scripts/phase6-verify-por.sh](../../scripts/phase6-verify-por.sh)

## Next

[Phase 7 — Production hardening](./PHASE-7.md): security, fleet ops, cold tier, Transynth prep.
