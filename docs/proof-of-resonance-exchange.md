# PoREX — Proof of Resonance Exchange

## Transitional Synthetic Assets (Transynths)

Transynths are digitally represented on-chain as **tX***, where * is a semantic asset-class suffix after the literal prefix `tX`. Naming rule: lowercase English words, except registered acronyms (`IREC`).

| Token ID | Asset class | Unit (Phase 1 spec) |
|----------|-------------|---------------------|
| **tXcarbon** | Carbon offsets | 1 tXcarbon = 1 ton CO₂e offset |
| **tXbiodiversity** | Biodiversity restoration | 1 tXbiodiversity = 0.1 hectares restored |
| **tXwater** | Water conservation | 1 tXwater = 1,000,000 liters conserved |
| **tXsoil** | Soil regeneration | 1 tXsoil = 1 hectare regenerated |
| **tXIREC** | I-REC renewable energy certificates | I-REC compliant renewable energy |
| **tXenergy** | Verified green energy production | Metered kWh / production telemetry |
| **tXtel** | Telecom provenance | Bandwidth, CDR-normalized usage evidence |

**Distinctions:**

- **tXIREC** — certificate-style renewable energy (I-REC standard).
- **tXenergy** — direct metered green energy from prosumer / utility telemetry (e.g. Bytenergy).
- **tXtel** — telecom DePIN and voice-lab provenance (Zeegate, Phase 2 CDR adapter).

CosmWasm crate paths use kebab-case (`tx-carbon/`, `tx-tel/`, …); on-chain token IDs use the **tX**{suffix} form above.

Mechanics
- Transynths (tX*) are minted by PoREX contracts when verified evidence from PoRE/PoREF meets thresholds.
- AMM + order book implemented via CosmWasm contracts for liquidity and trading.
- Retirement mechanism burns tokens upon confirmed corporate offset or consumption to avoid double-counting.

### Lab mint gates (tx-tel)

| Gate | Phase 1 lab default |
|------|---------------------|
| EQS | ≥ 0.70 |
| RIV | > 0 |
| Consensus Confidence | 1.0 (oracle) |
| Evidence Resonance | ≥ 50 |

Implemented in `contracts/tx-tel/` (on-chain) and mirrored off-chain for intent recording; with wasmd + `TX_TEL_CONTRACT`, the oracle bridge broadcasts `ExecuteMsg::Mint` (`COSMWASM-ENABLEMENT.md`).

Distribution
- Monthly distribution of newly minted Transynths (tX*): 60% miners, 20% DAO treasury, 15% validators, 5% community.

Native token (TEGAL)
- **TEGAL / uteg** is separate from Transynths — governance and utility, never pre-mined, impact-gated block issuance. See [TEGAL-TOKENS.md](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/contracts/TEGAL-TOKENS.md).

Stable value (Voixcoin)
- **Voixcoin** — minted only by locking **PA (Provenance Assets)** in the custodianless Greenledger collateral vault. See [VOIXCOIN.md](https://github.com/Shootle/sovereign-ecosystem/blob/main/docs/contracts/VOIXCOIN.md).

Compliance
- tX* redemption and retirement include audit trails, vintage metadata, and proofs stored in the PoREvidence registry (CosmWasm contract).
