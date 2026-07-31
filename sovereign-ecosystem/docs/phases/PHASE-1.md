# Phase 1 — Sovereign telemetry pipeline

**Status:** Complete (lab profile) — Replit mock drain verified 2026-07-27  
**Goal:** Signed telemetry → validate → mint (HTTP mint worker)  
**Stack:** [TP-107](../PROTOCOL-STACK.md#tp-107--sovereign-platforms) → [TP-101](../PROTOCOL-STACK.md#tp-101--greentelemetry) → [TP-103](../PROTOCOL-STACK.md#tp-103--greenledger) (Phase 1 slice)

## Directories added

```
integrations/
├── mint_worker/          # FastAPI service (Phase 1)
└── zeegate_telemetry/    # Zeegate producer (updated)

green_ledger_spec/        # TP-103 GLE, Carbon Accounts, integrity (Phase 1f)
tegalchain/greenledger/   # GLE archival bridge on submit

zeegate-cloud/            # Phase 2 voice lab (see PHASE-2.md)
```

## Run mint worker

```bash
cd /home/shootle/sovereign-ecosystem
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m integrations.mint_worker
```

Health check: `curl http://127.0.0.1:8090/health`

## Publish via worker

```bash
export MINT_WORKER_URL=http://127.0.0.1:8090
python integrations/zeegate_telemetry/client.py
python bytenergy-utility/client.py
```

## Exit criteria

- [x] Mint worker HTTP API (`POST /v1/telemetry`)
- [x] HMAC signature verification
- [x] Zeegate + Bytenergy clients can POST to worker
- [x] Android `TelemetryService` posts schema-valid signed payloads (**Phase 1b**)
- [x] Persist mint queue for Tegalchain submission (**Phase 1c**)
- [x] Tegalid mint gate + gretelemetry v1.1 optional fields (**Phase 1d**)
- [x] TP-101 canonical GTR v1 + legacy normalize ([TP-101-GREENTELEMETRY.md](../standards/TP-101-GREENTELEMETRY.md))
- [x] Ed25519 attestations over GTR canonical hash
- [x] TP-101 HTTPS REST ingestion (`POST /v1/telemetry/records`, batch, GET by `gtr_id`)
- [x] On-chain GTR anchor payload (`GTR_ANCHOR`: hash + summary only; full GTR in mint queue)
- [x] TP-101 security controls (Bearer auth, ±5 min attestation window, source rate limits, identity registry)
- [x] Unit test suite + GitHub Actions CI (`.github/workflows/ci.yml`)
- [x] TP-103 GLE archival on submit ([TP-103-GREENLEDGER.md](../standards/TP-103-GREENLEDGER.md)) — Auditrail + submitter drain → `greenledger_entries`
- [x] TP-103 Carbon Accounts, retention classes, and integrity checks (`green_ledger_spec/`, `tegalchain/greenledger/`)
- [x] Auditrail correlation after on-chain submit (`auditrail_correlations` table + GET `/records` field)
- [x] MQTT v5 ingestion bridge (`integrations/mint_worker/mqtt_bridge.py`)

### Phase 1 — still open (optional / production)

- [x] Live chain anchor with **`ledger_ref`** on Replit — verified with `TEGALCHAIN_SUBMITTER_BACKEND=mock` → `LABMOCK-…` + Auditrail + GLE on `GET /v1/telemetry/records/{gtr_id}` — runbook: [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md)
- [x] Anchor SLA watchdog (`sla-check`, `watch`, `GET /v1/queue/anchor-sla`)
- [ ] DID-based API authentication (Bearer OAuth 2.0 compatible path is live)
- [ ] Long-term cold-tier export / multi-site replication (7-year operational target beyond SQLite hot tier)

## Phase 1c — Mint queue → Tegalchain (Replit)

After mint, the worker enqueues `TELEMETRY_MINT` block candidates in SQLite (`tegalchain/data/mint_queue.db`, deduped by `telemetry_hash`). Drain to Tegalchain with:

```bash
export TEGALCHAIN_MINT_QUEUE_DB=tegalchain/data/mint_queue.db
export TEGALCHAIN_OUTBOX_DIR=tegalchain/data/outbox
export TEGALCHAIN_SUBMITTER_BACKEND=mock   # lab default — no Qortal on Replit

python -m tegalchain.submitter drain --limit 20
python -m tegalchain.submitter sla-check
python -m tegalchain.submitter watch --limit 20 --interval 30 --cycles 3
python -m tegalchain.submitter stats
```

Or:

```bash
./scripts/replit-mint-drain.sh 20
./scripts/replit-mint-watch.sh 20 30
```

Runbook: [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md). Legacy Qortal optional via `TEGALCHAIN_SUBMITTER_BACKEND=qortal`.

Without `TEGALCHAIN_SUBMITTER_BACKEND=mock`, unset backend + no privkey writes outbox only. With **mock** (Replit default), rows become **`submitted`** with `LABMOCK-…` refs + Auditrail correlation + TP-103 GLE archival. Legacy Qortal requires `TEGALCHAIN_SUBMITTER_BACKEND=qortal` and `TEGALCHAIN_PRIVKEY`.

Mint worker ops: `GET /v1/queue/stats`

## Phase 1e — TP-101 REST, anchoring, and security

Canonical GTR ingestion and on-chain anchor summary fields. Spec: [TP-101-GREENTELEMETRY.md](../standards/TP-101-GREENTELEMETRY.md).

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/telemetry/records` | Accept single GTR → `{ gtr_id, ledger_ref, queue_id, status }` |
| `POST` | `/v1/telemetry/batch` | Batch ingest (max 1,000 records) |
| `GET` | `/v1/telemetry/records/{gtr_id}` | Full GTR + attestations + `on_chain_anchor` + `greenledger_entry` |
| `POST` | `/v1/telemetry` | Legacy Phase 1 envelope (still supported) |

On ingest, the oracle embeds a `GTR_ANCHOR` in each `block_candidate` (`gtr_id`, `content_hash`, `attester_ids`, `measurement_type`, `timestamp`). The submitter sets `anchor_timestamp` at drain. Optional Merkle batching: `TEGALCHAIN_MERKLE_BATCH=1`.

Security env (production):

```bash
export MINT_WORKER_BEARER_TOKEN=...          # OAuth 2.0 Bearer on all REST routes
export TEGALCHAIN_REQUIRE_BEARER=1           # optional — force auth even without token file
export TEGALCHAIN_REQUIRE_SOURCE_REGISTRY=1  # require registered source_id
export TEGALID_SOURCE_REGISTRY_FILE=tegalchain/data/source_registry.example.json
cp tegalchain/data/source_registry.example.json tegalchain/data/source_registry.json
```

Run tests locally:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tegalchain -p 'test_*.py' -q
python -m unittest discover -s integrations/mint_worker -p 'test_*.py' -q
python -m unittest discover -s integrations/zeegate_telemetry -p 'test_*.py' -q
python -m unittest discover -s green_ledger_spec -p 'test_*.py' -q
```

## Phase 1d — Tegalid gate (greentelemetry v1.1)

Production mint requires **tegalid identity lock** for registered Greenledger projects. Tegalchain receives telemetry **only** via this oracle — subsystems remain independent. Contract: [docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md](../contracts/GREETELEMETRY-ORACLE-BOUNDARY.md), [TEGALID-GREETELEMETRY.md](../contracts/TEGALID-GREETELEMETRY.md).

```bash
cp tegalchain/data/tegalid_bindings.example.json tegalchain/data/tegalid_bindings.json
export TEGALCHAIN_IDENTITY_MODE=tegalid
export TEGALID_BINDINGS_FILE=tegalchain/data/tegalid_bindings.json
python -m integrations.mint_worker
```

- `node_id` must be `did:tegal:…` with an active `NodeBinding`
- Optional v1.1 fields: `project_id`, `binding_id`
- Per-binding HMAC secret (not the dev key)
- Mint worker returns **403** if not mint-eligible

Local dev (default): `TEGALCHAIN_IDENTITY_MODE=dev` — legacy `node_id` + shared dev HMAC.

ZK (optional): `TEGALCHAIN_ZK_MODE=off|dev|required` — see [GREETELEMETRY-ZK.md](../contracts/GREETELEMETRY-ZK.md). ZK binds **final public evidence** to the Greenledger, including adapter-normalized CDR; raw subsystem data never crosses the boundary.

Tegalchain protocol (transactions, blocks, finality, lifecycle, endorsement policies, contract lifecycle, contract interface, contract best practices, client applications, state database, state access patterns, network configuration, protocol upgrades, access control lists, gossip): [TEGALCHAIN.md](../TEGALCHAIN.md).

## Phase 1b — Android greentelemetry

`TelemetryService` builds `SovereignNodeTelemetry` for `ZEEGATE_TELECOM`:

- `node_id`, `timestamp` (seconds), `metrics.telecom_bandwidth_bytes`, HMAC signature
- Bandwidth from `TrafficStats` UID counters (AnyFi/SIP share app UID)
- POST to mint worker (`BuildConfig.MINT_WORKER_BASE_URL` or `TelemetryService.configure()`)

Lab: run mint worker on host, use emulator URL `http://10.0.2.2:8090`.

## Phase 1f — TP-103 GreenLedger (GLE archival)

Spec: [TP-103-GREENLEDGER.md](../standards/TP-103-GREENLEDGER.md).

After on-chain submit, the submitter drain and Auditrail correlation archive each anchored GTR as a **GreenLedger Entry (GLE)** in SQLite (`greenledger_entries`), refresh the source **Carbon Account**, and expose the entry on record lookup.

| Component | Location |
|-----------|----------|
| Normative spec + schema | [TP-103-GREENLEDGER.md](../standards/TP-103-GREENLEDGER.md), [green-ledger-spec/](../../green-ledger-spec/) |
| GLE builder + retention | [green_ledger_spec/](../../green_ledger_spec/) |
| Archive bridge | [tegalchain/greenledger/](../../tegalchain/greenledger/) |
| Store + query | [tegalchain/queue/store.py](../../tegalchain/queue/store.py) (`greenledger_entries`, `carbon_accounts`, `greenledger_integrity_violations`) |
| Auditrail wiring | [tegalchain/auditrail.py](../../tegalchain/auditrail.py) |

Phase 1 profile: SQLite hot tier (24-month classification), `STANDARD` 7-year retention policy in code, integrity schedules via `green_ledger_spec/integrity.py`. Cold-tier export and ≥2-site replication remain deployment targets.

Verify after drain:

```bash
python -m tegalchain.submitter drain --limit 20
curl -s "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | jq '.greenledger_entry'
```

## Next

See [phases/README.md](./README.md) for the full roadmap (Phases 3–7).

1. **[Phase 3 — Live voice CDR](./PHASE-3.md)** — Docker `zeegate_cdr` → adapter → mock `ledger_ref`
2. **[Phase 4 — DePIN edge producers](./PHASE-4.md)** — Android Zeegate + Bytenergy → mint worker
3. **[Phase 5 — Cosmos devnet anchor](./PHASE-5.md)** — real `txhash` instead of `LABMOCK-…`
4. **TP-103 ops (optional)** — cold-tier export, integrity cron, Carbon Account HTTP — rolled into [Phase 7](./PHASE-7.md)
5. **Production hardening (optional)** — Bearer auth, tegalid default — [Phase 7](./PHASE-7.md)
