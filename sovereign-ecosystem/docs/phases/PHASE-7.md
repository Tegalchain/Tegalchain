# Phase 7 — Production hardening & fleet ops

**Status:** In progress — **staging lab verified** 2026-07-29  
**Proof `gtr_id`:** `bd1a476b-a8a1-4edc-89b9-50b205adf72f` — tegalid + Bearer ingest → GLE + Carbon Account (`did:tegal:LABEDGE001`)
**Depends on:** Phases 1–6 complete (lab)  
**Goal:** Operate the sovereign stack **beyond lab profile** — auth, continuous drain, retention export, and TP-104+ readiness  
**Stack:** TP-101 security · TP-103 ops · TP-104 tX* · TP-106 governance policy

Phase 7 hardens **provenance ops** only. It **MUST NOT** introduce custodial behavior — see [TP-103 § Custodianless by design](../standards/TP-103-GREENLEDGER.md#custodianless-by-design). Bearer auth, integrity cron, cold export, and Carbon Account HTTP are archival and access-control concerns; tX* mint and PA collateral remain **TP-104 / TP-105**.

## Scope

| Track | Items | Status |
|-------|-------|--------|
| **Security** | `MINT_WORKER_BEARER_TOKEN`, `TEGALCHAIN_REQUIRE_BEARER=1`, TLS 1.3+ termination | **Staging scripts live** — enforce via prod start |
| **Identity** | Default `TEGALCHAIN_IDENTITY_MODE=tegalid`, on-chain binding cache REST | Lab JSON cache live |
| **Ops** | `replit-mint-watch.sh`, anchor SLA alerts, queue metrics | Watch + SLA live; queue routes bearer-gated |
| **TP-103 cold tier** | GLE export adapter, scheduled integrity cron, Carbon Account HTTP API | **Live** (Phase 7 start) |
| **Fleet** | MQTT fleet ingest, multi-source registry, rate-limit tuning | Partial |
| **TP-104** | tX* CosmWasm contracts (`tx-carbon`, `tx-tel`, …) | Specified — deploy on devnet |
| **DID API auth** | Tegalchain-native DID bearer (replaces shared secret) | **Open** |

## Phase 7 deliverables (this slice)

| Component | Location |
|-----------|----------|
| Prod/staging start | `scripts/start-mint-worker-prod.sh`, `restart-mint-worker-prod.sh` |
| Staging verify | `scripts/phase7-verify-staging.sh` |
| Staging ingest + GLE | `scripts/phase7-staging-ingest.sh` |
| Bearer on ops routes | `GET /v1/queue/stats`, `GET /v1/queue/anchor-sla` |
| Carbon Account HTTP | `GET /v1/greenledger/carbon-accounts/{source_id}` |
| Integrity CLI | `python -m tegalchain.greenledger integrity-check` |
| Cold export CLI | `python -m tegalchain.greenledger export-cold` |
| Soak runbook | [PHASE-7-STAGING-SOAK.md](../runbooks/PHASE-7-STAGING-SOAK.md) |
| Soak watch + verify | `scripts/phase7-soak-watch.sh`, `scripts/phase7-soak-verify.sh` |
| Replit sync check | `scripts/replit-sync-check.sh` |

## Security baseline

```bash
export MINT_WORKER_BEARER_TOKEN="$(openssl rand -hex 24)"   # save echoed value
export TEGALCHAIN_REQUIRE_BEARER=1
export TEGALCHAIN_IDENTITY_MODE=tegalid
export TEGALID_BINDINGS_FILE=tegalchain/data/tegalid_bindings.example.json
./scripts/start-mint-worker-prod.sh
```

All producers (CDR adapter, Android, Bytenergy) must send `Authorization: Bearer <token>` on REST. MQTT uses password / token per [TP-101](../standards/TP-101-GREENTELEMETRY.md).

`/health` stays public for liveness probes; all telemetry, queue, and greenledger routes require Bearer when configured.

## Run (Replit / WSL)

### Shell 1 — staging worker

```bash
cd ~/workspace/sovereign-ecosystem
git pull origin main
./scripts/replit-sync-check.sh
export MINT_WORKER_BEARER_TOKEN="$(openssl rand -hex 24)"   # save echoed value
./scripts/restart-mint-worker-prod.sh
```

### Shell 2 — verify

Use the **same hex token** from Shell 1 (not doc placeholders):

```bash
export MINT_WORKER_BEARER_TOKEN=<paste-saved-hex-from-shell-1>
./scripts/phase7-verify-staging.sh staging
```

### Shell 2b — full staging path (ingest → drain → GLE + Carbon Account)

```bash
export MINT_WORKER_BEARER_TOKEN=<paste-saved-hex-from-shell-1>
./scripts/phase7-staging-ingest.sh
```

### 24h soak (Shell 2)

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=mock   # or cosmos
./scripts/phase7-soak-watch.sh 20 30
```

After ≥24h, mark complete:

```bash
export MINT_WORKER_BEARER_TOKEN=<paste-saved-hex-from-shell-1>
./scripts/phase7-soak-verify.sh
```

Lab shortcut: `REPLIT_SOAK_HOURS=1` on both watch and verify. See [PHASE-7-STAGING-SOAK.md](../runbooks/PHASE-7-STAGING-SOAK.md).

### Continuous watch (no soak log)

```bash
./scripts/replit-mint-watch.sh 20 30
# optional TP-103 integrity each cycle:
PHASE7_INTEGRITY=1 ./scripts/replit-mint-watch.sh 20 30 5
```

Lab worker (no bearer) still works:

```bash
./scripts/start-mint-worker.sh
./scripts/phase7-verify-staging.sh lab
```

See [PHASE-7-STAGING-SOAK.md](../runbooks/PHASE-7-STAGING-SOAK.md) for 24h soak criteria.

## TP-103 ops commands

```bash
# Scheduled integrity (exit 2 on violations)
python3 -m tegalchain.greenledger integrity-check --schedule DAILY

# Cold-tier JSONL export (upload to object storage in prod)
python3 -m tegalchain.greenledger export-cold --output-dir tegalchain/data/cold_export

# Carbon Account HTTP
curl -s -H "Authorization: Bearer $MINT_WORKER_BEARER_TOKEN" \
  "http://127.0.0.1:8090/v1/greenledger/carbon-accounts/zerocell-node-001" | python3 -m json.tool
```

Requires at least one drained GLE for carbon account data.

## TP-104 Transynth prep

Deploy tX* contracts on devnet; map GLE + PoRE scores to mint eligibility:

| Token | Vertical | Evidence |
|-------|----------|----------|
| `tXtel` | Zeegate telecom | CDR + bandwidth GTRs |
| `tXcarbon` | Carbon / energy | Bytenergy + GLE |
| … | See [GLOSSARY](../GLOSSARY.md) | TP-102 thresholds |

CosmWasm paths: `tegalchain-core/contracts/tx-*/`.

## Exit criteria

- [x] `./scripts/phase7-verify-staging.sh staging` passes with prod worker
- [x] `./scripts/phase7-staging-ingest.sh` → GLE + Carbon Account (`bd1a476b-a8a1-4edc-89b9-50b205adf72f`)
- [x] Bearer required on telemetry + queue + greenledger routes in staging
- [x] `tegalid` mode default in prod start script; dev mode for lab only
- [ ] Continuous watch + SLA runbook exercised 24h soak (`phase7-soak-verify.sh` passes)
- [x] Cold-tier export job documented + CLI tested
- [x] Integrity cron CLI wired to `green_ledger_spec/integrity.py`
- [x] Carbon Account HTTP endpoint live
- [ ] (Optional) One tX* contract mint from devnet GLE correlation

## Tests

```bash
python3 -m unittest tegalchain.test_greenledger_ops integrations.mint_worker.test_server -v
python3 -m tegalchain.greenledger integrity-check --schedule DAILY
```

## Related

- [PHASE-6.md](./PHASE-6.md) — TP-102 PoR (complete)
- [PHASE-1.md](./PHASE-1.md) — optional production items
- [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md)
- [TP-103-GREENLEDGER.md](../standards/TP-103-GREENLEDGER.md)

## Beyond Phase 7

- [Phase 8 — TP-108 AI attestation (lab stub)](./PHASE-8.md) — **complete** (`70206e10-205b-47f3-8e87-00e2914b115a`)
- **TP-105 Voixcoin** — PA-collateralized stablecoin on Greenledger
- **TP-106 TEGAL DAO** — uteg governance, impact-gated issuance
- Multi-node DePIN fleet at scale (Zeegate v2 cloud integration)

Track in [PROTOCOL-STACK.md](../PROTOCOL-STACK.md) and `tegalchain-core` roadmap.
