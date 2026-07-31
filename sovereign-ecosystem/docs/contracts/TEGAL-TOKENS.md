# TEGAL tokens — governance and utility

**Status:** Contract (chain implementation on Tegalchain Greenledger)  
**Scope:** Native Tegalchain tokens — **not** Transynths (tX*) and **not** subsystem-internal assets

## What TEGAL is

**TEGAL** is the native **governance and utility** token of the Tegalchain ecosystem. It coordinates DAO decisions, pays for protocol utility (fees, staking, participation), and rewards **verified impact work** — not speculative issuance.

| Denom | Role |
|-------|------|
| **TEGAL** | Base unit — governance votes, treasury, block-impact allocation |
| **uteg** | Smallest on-chain denom (micro-TEGAL) |

Transynths (**tX***) represent environmentally provenance impact assets. TEGAL represents **network participation and governance** over that ledger. **Voixcoin** is the PA-collateralized stable value unit on the custodianless Greenledger — see [VOIXCOIN.md](./VOIXCOIN.md). See also [GREETELEMETRY-ZK.md](./GREETELEMETRY-ZK.md) and [tegalchain-core/docs/proof-of-resonance-exchange.md](../../tegalchain-core/docs/proof-of-resonance-exchange.md).

## Non-negotiable issuance rule

**TEGAL is never pre-mined.**

There is no genesis allocation, ICO, or founder mint. Every uteg in circulation must trace to one of the allowed acquisition paths below.

## How TEGAL is acquired (only these paths)

```text
                    ┌─────────────────────────────────┐
                    │  TEGAL / uteg in circulation     │
                    └─────────────────────────────────┘
                           ▲         ▲         ▲
                           │         │         │
              block creation   exchange    burn technology
              (impact work)    purchase    (DAO-governed)
```

| Path | Description |
|------|-------------|
| **Block creation (impact)** | New blocks mint TEGAL/uteg only when tied to **verified impact** — node operator work (gretelemetry, validation, evidence) and **DAO-approved** ecosystem participation incentives |
| **Exchange purchase** | Secondary market acquisition on PoREX / approved venues — no protocol pre-sale |
| **Burn technology** | On-chain burn and redemption flows (e.g. retirement, fee recycle, collateral release) that allocate or unlock TEGAL per **DAO-governed** rules — not discretionary mint |

Acquisition paths **exclude** discretionary admin mint, airdrops outside DAO vote, and unbacked inflation.

## Block creation and impact

Each new block may allocate TEGAL/uteg to participants whose work is **evidence-backed**:

1. **Node operators** — tegalid-bound producers whose signed gretelemetry (and optional ZK) passes the oracle gate ([TEGALID-GREETELEMETRY.md](./TEGALID-GREETELEMETRY.md)).
2. **Validators / PoREF** — consensus and evidence verification per PoR stack.
3. **Ecosystem participation** — contributors approved by **DAO governance** (reviews, adapters, audits, community programs).

Impact scoring (EQS, RIV, consensus confidence) informs allocation; the DAO sets emission policy. Issuance follows **work and verified evidence**, not price speculation.

```text
Verified work / gretelemetry → PoRE evidence → block proposal
        → DAO emission policy → TEGAL/uteg credited to eligible addresses
```

Phase 1 bridge (`tegalchain/mint.py`) emits **TELEMETRY_MINT** evidence candidates — not TEGAL coin mint. On-chain TEGAL credit is a **future chain module** fed by oracle-verified impact.

## Real-world assets, not speculation

Design intent:

- **Transynths (tX*)** tokenize proven environmental outcomes with retirement and audit trails.
- **TEGAL** incentivizes honest operation and governance over that ledger.
- **No pre-mine** prevents insider supply shocks.
- **Impact-gated block rewards** tie issuance to measurable DePIN/utility work.
- **DAO approval** for participation incentives keeps discretionary mint out of operator hands.

Speculative trading may occur on exchanges, but **protocol issuance does not target traders** — it targets operators and contributors with verified impact.

## Governance

- TEGAL holders vote on emission parameters, treasury, participation incentive programs, and burn/redemption policy.
- See [tegalchain-core/GOVERNANCE.md](../../tegalchain-core/GOVERNANCE.md) for roles and dispute resolution.

## Related

- [VOIXCOIN.md](./VOIXCOIN.md) — PA-collateralized stablecoin on the custodianless Greenledger
- [GREETELEMETRY-ORACLE-BOUNDARY.md](./GREETELEMETRY-ORACLE-BOUNDARY.md) — evidence ingress only
- [TEGALID-GREETELEMETRY.md](./TEGALID-GREETELEMETRY.md) — identity lock before mint eligibility
- [tegalchain-core/docs/proof-of-resonance-stack.md](../../tegalchain-core/docs/proof-of-resonance-stack.md) — PoRE / PoREF / PoREX
