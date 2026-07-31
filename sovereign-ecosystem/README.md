# Sovereign Ecosystem

Multi-layered sovereign stack for **environmentally sustainable DePIN and utility projects**: Zerocell Zeegate (telecom), Bytenergy (energy), **Tegalchain** (permissioned ledger / Greenledger), and extensible greentelemetry telemetry for future nodes.

**Protocol stack:** TP-101 GreenTelemetry → TP-102 PoR → TP-103 GreenLedger → TP-104 Transynth → TP-105 Voixcoin → TP-106 TEGAL DAO → TP-107 Sovereign Platforms — [docs/PROTOCOL-STACK.md](docs/PROTOCOL-STACK.md).

**What is Tegalchain?** Permissioned distributed ledger for auditable multi-party record-keeping — [docs/TEGALCHAIN.md](docs/TEGALCHAIN.md).

**Glossary:** `gretelemetry` = greentelemetry protocol; `GreTelemetry` = Zeegate Android client — [docs/GLOSSARY.md](docs/GLOSSARY.md).

## Layout

| Path | Role |
|------|------|
| `greentelemetry-protocol-spec/` | Canonical JSON Schema (`schema.json`) |
| `greentelemetry_protocol_spec/` | Python validation, models, and signing |
| `integrations/mint_worker/` | **Gretelemetry oracle** — validate, tegalid gate, mint ingress |
| `integrations/zeegate_telemetry/` | Zeegate Python telemetry producer |
| `tegalchain/` | Gretelemetry oracle bridge → tegalid gate → mint queue (no subsystem coupling) |
| `tegalchain-core/` | Git submodule → [Tegalchain/Tegalchain](https://github.com/Tegalchain/Tegalchain) — permissioned ledger core; Replit target |
| `zeegate/` | **Android Studio** — DePIN edge: gsm2sip + AnyFi WiFi gateway + GreTelemetry |
| `zeegate-cloud/` | **Phase 2** — Kamailio SBC + FreeSWITCH media lab (`deploy/docker-compose.yml`) |
| `bytenergy-utility/` | Bytenergy prosumer energy telemetry client |

All subsystems communicate exclusively via [greentelemetry-protocol-spec/schema.json](greentelemetry-protocol-spec/schema.json) — one contract for Zeegate, Bytenergy, and future sustainable project types.

**Tegalchain boundary:** chain logic connects to projects **only** through the gretelemetry oracle/adapter ([docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md](docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md)). Subsystems are independent.

Tegalid identity lock for mint: [docs/contracts/TEGALID-GREETELEMETRY.md](docs/contracts/TEGALID-GREETELEMETRY.md)  
ZK on final Greenledger evidence: [docs/contracts/GREETELEMETRY-ZK.md](docs/contracts/GREETELEMETRY-ZK.md)  
TEGAL governance/utility tokens (uteg, no pre-mine): [docs/contracts/TEGAL-TOKENS.md](docs/contracts/TEGAL-TOKENS.md)  
Voixcoin (PA-collateralized stablecoin, custodianless Greenledger): [docs/contracts/VOIXCOIN.md](docs/contracts/VOIXCOIN.md)

Versioning policy: [docs/VERSIONING.md](docs/VERSIONING.md) · component versions: [VERSIONS.json](VERSIONS.json)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# After clone, initialize the blockchain submodule:
git submodule update --init --recursive

# Phase 1 — run mint worker (separate terminal):
python -m integrations.mint_worker
```

## Sync with Replit

Replit workspace path: `~/workspace/sovereign-ecosystem` (or clone this repo).

```bash
cd ~/workspace/sovereign-ecosystem
./scripts/replit-update.sh
# or: git pull origin main && ./scripts/replit-sync-check.sh
pip install -r requirements.txt   # if deps changed
```

**Phase 7 staging (prod profile on Replit):**

```bash
# Shell 1
export MINT_WORKER_BEARER_TOKEN=$(openssl rand -hex 24)
echo "$MINT_WORKER_BEARER_TOKEN"   # save for Shell 2
./scripts/restart-mint-worker-prod.sh

# Shell 2 — use the echoed token, not doc placeholders
export MINT_WORKER_BEARER_TOKEN=<paste-saved-hex-from-shell-1>
./scripts/phase7-verify-staging.sh staging
./scripts/phase7-staging-ingest.sh
```

Lab profile (Phases 1–6, no Bearer): `./scripts/start-mint-worker.sh`  
Runbook index: [docs/phases/README.md](docs/phases/README.md) · [PHASE-8.md](docs/phases/PHASE-8.md) (TP-108 lab stub) · [LAB-MINT-DRAIN.md](docs/runbooks/LAB-MINT-DRAIN.md) · [PHASE-7-STAGING-SOAK.md](docs/runbooks/PHASE-7-STAGING-SOAK.md)

Replit also hosts **tegalchain-core** (`Tegalchain/Tegalchain`) — this monorepo adds the gretelemetry oracle and DePIN clients on top. Push changes here to GitHub, then `git pull` on Replit.

## Android Studio (Zeegate)

The native app lives in `zeegate/`. Open that folder in Android Studio; open the monorepo root in Cursor. Both share this Git repo — push/pull via GitHub to stay in sync.

See [zeegate/README.md](zeegate/README.md) for SDK setup and WSL paths.
