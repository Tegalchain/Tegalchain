# Glossary

## Protocol stack (TP standards)

Canonical layer index: [PROTOCOL-STACK.md](./PROTOCOL-STACK.md).

| ID | Standard | One-line purpose |
|----|----------|------------------|
| **TP-101** | GreenTelemetry | Signed **GTR** evidence envelope from sovereign nodes — [TP-101-GREENTELEMETRY.md](./standards/TP-101-GREENTELEMETRY.md) |
| **TP-102** | Proof of Resonance | PoRE / PoREF / PoREX — trust and impact verification — [TP-102-PROOF-OF-RESONANCE.md](./standards/TP-102-PROOF-OF-RESONANCE.md) |
| **TP-103** | GreenLedger | Provenance archive (GLE, Auditrail) — [TP-103-GREENLEDGER.md](./standards/TP-103-GREENLEDGER.md) |
| **TP-104** | Transynth Standard | tX* environmentally provenance assets |
| **TP-105** | Voixcoin | PA-collateralized stable value, custodianless vault |
| **TP-106** | TEGAL DAO | TEGAL / uteg governance, no pre-mine |
| **TP-107** | Sovereign Platforms | Independent subsystems (Zeegate, Bytenergy, …) as gretelemetry producers |
| **TP-108** | AI Attestation | Optional `THIRD_PARTY` ML/rule attestations on GTR metadata — [TP-108-AI-ATTESTATION.md](./standards/TP-108-AI-ATTESTATION.md) |

## Naming

**gretelemetry** = **greentelemetry protocol** (docs/oracle shorthand); **`GreTelemetry`** = Zeegate Android client helper (Kotlin). Full protocol paths and packages use `greentelemetry`.

**GTR (GreenTelemetry Record)** = TP-101 atomic evidence unit (`schema_version: "1.0"`) with `gtr_id`, `source_id`, `measurement_type`, `value`, `unit`, ISO `timestamp`, and `attestations`. Legacy `SovereignNodeTelemetry` envelopes are normalized to GTR at the oracle. See [standards/TP-101-GREENTELEMETRY.md](./standards/TP-101-GREENTELEMETRY.md).

The chain ledger application is **Greenledger** (full “Green” spelling) — not the same word as the protocol prefix `gre-`.

**Tegalchain** = permissioned ledger **core** (TP-103 infrastructure). **Greenledger** = environmental/provenance **application** running on that core (gretelemetry oracle, Auditrail, PoR, Transynths, Voixcoin, TEGAL).

**PoR stack** (TP-102 sub-layers): **PoRE** (evidence), **PoREF** (foundation validators), **PoREX** (exchange / tX* tokenization).

**Transynths (tX***)** = transitional synthetic provenance assets (TP-104). Token IDs use the form **tX**{suffix} — lowercase words, except registered acronyms (`IREC`):

| Token ID | Asset class |
|----------|-------------|
| **tXcarbon** | Carbon offsets |
| **tXbiodiversity** | Biodiversity restoration |
| **tXwater** | Water conservation |
| **tXsoil** | Soil regeneration |
| **tXIREC** | I-REC renewable energy certificates |
| **tXenergy** | Verified green energy (metered kWh / production) |
| **tXtel** | Telecom provenance (Zeegate, CDR adapter) |

**PA** = Provenance Assets eligible as Voixcoin collateral (TP-105).
