# Sovereign ecosystem — delivery phases

Phases are **incremental lab → production slices** across [TP-107](../PROTOCOL-STACK.md#tp-107--sovereign-platforms) producers, [TP-101](../standards/TP-101-GREENTELEMETRY.md) evidence, and [TP-103](../standards/TP-103-GREENLEDGER.md) anchoring. Subsystems never talk to the ledger directly — all paths go through the gretelemetry oracle (`integrations/mint_worker/`).

## Roadmap

| Phase | Name | Status | Anchor backend | Primary proof |
|-------|------|--------|----------------|---------------|
| **1** | [Telemetry pipeline](./PHASE-1.md) | **Complete** (lab) | `LABMOCK-…` | Client GTR → queue → drain → GLE |
| **2** | [Zeegate cloud voice](./PHASE-2.md) | **Complete** (lab) | `LABMOCK-…` | CDR fixture → adapter → `ledger_ref` |
| **3** | [Live voice CDR](./PHASE-3.md) | **Complete** (lab) | `LABMOCK-…` | Docker `zeegate_cdr` → call → drain |
| **4** | [DePIN edge producers](./PHASE-4.md) | **Complete** (Track A lab) | `LABMOCK-…` | Python edge sim → mint worker |
| **5** | [Cosmos devnet anchor](./PHASE-5.md) | **Complete** (lab stub) | `txhash` | Cosmos REST drain → hex `ledger_ref` |
| **6** | [TP-102 Proof of Resonance](./PHASE-6.md) | **Complete** (lab) | either | PoRE RFM on GET `por_scores` |
| **7** | [Production hardening](./PHASE-7.md) | **In progress** (staging verified) | production | tegalid + Bearer → GLE + Carbon Account |
| **8** | [TP-108 AI attestation](./PHASE-8.md) | **Complete** (lab stub) | either | CDR ↔ bandwidth `CORROBORATION` on GTR |

```text
Phase 1 ──► mint worker + queue + mock drain + GLE
Phase 2 ──► voice stack + CDR adapter (fixture proved)
Phase 3 ──► live SIP call → real CDR volume → same mock path
Phase 4 ──► Zeegate Android + Bytenergy → same oracle
Phase 5 ──► Cosmos REST drain → txhash ledger_ref (lab stub; devnet target)
Phase 6 ──► TP-102 PoRE on verified GTRs
Phase 7 ──► Bearer auth, cold tier, continuous ops, tX* prep
Phase 8 ──► TP-108 optional THIRD_PARTY AI attestations (lab stub)
```

## Lab defaults (Phases 1–4)

| Setting | Lab value |
|---------|-----------|
| Submitter | `TEGALCHAIN_SUBMITTER_BACKEND=mock` |
| Identity | `TEGALCHAIN_IDENTITY_MODE=dev` (CDR: binding secret lookup ≥ `5f6c9f5`) |
| Drain | [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md) |
| Mint worker | `python3 -m integrations.mint_worker` on `:8090` |

## Related

- [PROTOCOL-STACK.md](../PROTOCOL-STACK.md) — TP-101 … TP-107 standards map
- [VERSIONING.md](../VERSIONING.md) — component version lines
- [VERSIONS.json](../../VERSIONS.json) — pinned component versions
