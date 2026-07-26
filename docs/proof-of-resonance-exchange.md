# PoREX — Proof of Resonance Exchange

## Transitional Synthetic Assets (Transynths)

Transynths are digitally represented on-chain as **tX***, where * stands for multiple types of environmentally provenance assets. Examples:

- tXc — carbon (1 tXc = 1 ton CO₂e offset)
- tXb — biodiversity (1 tXb = 0.1 hectares restored)
- tXw — water (1 tXw = 1,000,000 liters conserved)
- tXs — soil (1 tXs = 1 hectare regenerated)
- tXi — I-REC (I-REC compliant renewable energy)

Mechanics
- Transynths (tX*) are minted by PoREX contracts when verified evidence from PoRE/PoREF meets thresholds.
- AMM + order book implemented via CosmWasm contracts for liquidity and trading.
- Retirement mechanism burns tokens upon confirmed corporate offset or consumption to avoid double-counting.

Distribution
- Monthly distribution of newly minted Transynths (tX*): 60% miners, 20% DAO treasury, 15% validators, 5% community.

Compliance
- tX* redemption and retirement include audit trails, vintage metadata, and proofs stored in the PoREvidence registry (CosmWasm contract).
