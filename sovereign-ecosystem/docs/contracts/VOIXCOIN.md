# Voixcoin — PA-collateralized stable value on the Greenledger

**Status:** Contract (chain implementation on Tegalchain Greenledger)  
**Scope:** Stable value unit backed by **Provenance Assets (PA)** locked in the **custodianless** Greenledger

## What Voixcoin is

**Voixcoin** is Tegalchain’s stablecoin. It is **derived only by collateralizing PA assets** into a **secured, non-custodial** position on the Greenledger.

There is no off-ledger custodian holding PA on behalf of users. Collateral remains **on-chain** under protocol rules (lock, audit trail, ZK/tegalid bindings where applicable). The Greenledger is **custodianless** — possession and release of PA are enforced by chain logic and Auditrail evidence, not by a trusted third party.

| Asset | Role |
|-------|------|
| **PA (Provenance Assets)** | Verified environmental provenance units — primarily **Transynths (tX***)** and DAO-registered PA types with Auditrail + PoRE evidence |
| **Voixcoin** | Stable value token minted **against locked PA**; redeemed by burning Voixcoin and unlocking collateral |

Voixcoin is **not** TEGAL (governance/utility) and **not** a pre-minted stablecoin allocation. See [TEGAL-TOKENS.md](./TEGAL-TOKENS.md).

## Custodianless Greenledger model

```text
Holder PA (tX* / registered PA)
        │
        ▼
Lock PA in Greenledger collateral vault (on-chain, non-custodial)
        │  · tegalid-bound identity
        │  · Auditrail + optional ZK on final evidence
        │  · liquidation / health factor per DAO params
        ▼
Mint Voixcoin (stable unit) to locker's address
        │
        ▼
Use / transfer Voixcoin (payments, PoREX, ecosystem utility)
        │
        ▼
Redeem: burn Voixcoin → unlock PA back to holder (minus fees/retirement policy)
```

**Non-custodial** means:

- PA never leaves the Greenledger’s collateral module while backing Voixcoin
- No central wallet or exchange holds PA as “custodian” for the protocol
- Lock/unlock is **transactional and auditable** (Auditrail + collateral state)
- Subsystems (Zeegate, Bytenergy, etc.) do not custody PA — only the oracle path posts **final evidence**; PA tokens live on-chain

## Provenance Assets (PA)

**PA** denotes on-ledger provenance-backed assets acceptable as Voixcoin collateral. Primary form:

- **Transynths (tX***)** — `tXcarbon`, `tXbiodiversity`, `tXwater`, `tXsoil`, `tXIREC`, `tXenergy`, `tXtel` ([proof-of-resonance-exchange.md](../../tegalchain-core/docs/proof-of-resonance-exchange.md))

Additional PA types may be registered by **DAO governance** if they meet:

1. Verified PoRE / Auditrail evidence
2. Registered `circuit_id` / asset class on Greenledger
3. Documented retirement and double-counting rules

Raw subsystem exports (CDR rows, meter blobs) are **never** PA — only adapter-normalized, ZK-wrapped **final evidence** that mints or registers tX* / PA on-chain.

## Mint and redeem (collateral technology)

| Action | Requirement |
|--------|-------------|
| **Mint Voixcoin** | Lock eligible PA at or above DAO **collateral ratio**; PA moves to secured vault state |
| **Redeem / unlock PA** | Burn Voixcoin; protocol releases proportional PA if position remains healthy |
| **Liquidation** | If collateral value (RIV / oracle marks) falls below threshold, DAO-defined liquidation protects Voixcoin solvency |

Collateral **locking and unlocking** for PA integration is the on-chain counterpart to Replit `replit-agent` provenance work — must align with this contract when merged to `master`.

Voixcoin supply is **fully backed** by locked PA on the Greenledger (over-collateralization optional per DAO).

## Relationship to other tokens

```text
┌─────────────────────────────────────────────────────────────┐
│                  Tegalchain Greenledger (custodianless)        │
├─────────────────────────────────────────────────────────────┤
│  TEGAL / uteg     governance + utility (impact mint, no pre-mine) │
│  Transynths tX*   PA — proven environmental units              │
│  Voixcoin         stable value — minted only vs locked PA       │
└─────────────────────────────────────────────────────────────┘
         ▲                              │
         │ gretelemetry oracle          │ lock PA → mint Voix
         │ (evidence only)              │
   Independent subsystems          PoREX / collateral module
```

- **TEGAL** — earned via impact block creation; votes on Voixcoin collateral parameters
- **Transynths** — impact assets; primary PA collateral for Voixcoin
- **Voixcoin** — liquidity/stable unit for real-world settlement without abandoning provenance backing

## Real-world assets, not speculation

Voixcoin is designed for **utility and settlement** backed by **verified provenance**, not unbacked stablecoin mint:

- Every Voixcoin maps to **locked PA** visible on-chain
- PA itself requires PoRE evidence and (where policy requires) ZK + tegalid
- No pre-mine of Voixcoin; mint only on collateral deposit
- DAO sets accepted PA types, ratios, and oracles — not discretionary admin mint

Secondary trading of Voixcoin may occur on PoREX; **protocol mint remains collateral-gated**.

## Governance

DAO votes on:

- Eligible PA asset types and haircuts
- Minimum collateral ratio and liquidation parameters
- Voixcoin peg / unit definition (e.g. USD reference via oracle policy)
- Fees on mint/redeem and treasury routing

## Related

- [TEGAL-TOKENS.md](./TEGAL-TOKENS.md) — governance/utility native token
- [GREETELEMETRY-ZK.md](./GREETELEMETRY-ZK.md) — ZK on final evidence for PA registration
- [TEGALID-GREETELEMETRY.md](./TEGALID-GREETELEMETRY.md) — identity lock
- [GREETELEMETRY-ORACLE-BOUNDARY.md](./GREETELEMETRY-ORACLE-BOUNDARY.md) — subsystems stay off-ledger
- [tegalchain-core/docs/proof-of-resonance-exchange.md](../../tegalchain-core/docs/proof-of-resonance-exchange.md) — Transynths / PoREX
