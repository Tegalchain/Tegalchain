# Contracts Workspace

This folder contains CosmWasm contracts for the Tegalchain PoR stack. Each contract is a Rust crate with a `src/` directory, `Cargo.toml` and tests.

Planned Transynth contracts (on-chain token IDs → workspace crate paths):

| Token ID | Crate path | Description |
|----------|------------|-------------|
| **tXcarbon** | `tx-carbon/` | Carbon Transynth |
| **tXbiodiversity** | `tx-biodiversity/` | Biodiversity Transynth |
| **tXwater** | `tx-water/` | Water Transynth |
| **tXsoil** | `tx-soil/` | Soil Transynth |
| **tXIREC** | `tx-irec/` | I-REC Transynth |
| **tXenergy** | `tx-energy/` | Green energy production Transynth |
| **tXtel** | `tx-tel/` | Telecom provenance Transynth |

Shared infrastructure crates:

- `token-factory/`
- `por-evidence-registry/`
- `poref-validation/`
- `impact-market/`
- `token-retirement/`
- `validator-slashing/`
- `reward-distribution/`

See contracts/DEVELOPMENT.md for setup and build instructions.
