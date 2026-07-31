# Lab mint drain runbook (no Qortal required)

Operational checklist for **Phase 1 closure** on Replit, WSL, or CI — using the **lab mock submitter** or optional **Cosmos REST** backend.

Qortal (`tx.pl` + Java node) is **legacy optional**. Replit free tier should use **`TEGALCHAIN_SUBMITTER_BACKEND=mock`** (default in `scripts/replit-mint-drain.sh`).

## Submitter backends

| Backend | Env | Needs node? | `ledger_ref` format |
|---------|-----|-------------|---------------------|
| **mock** (default lab) | `TEGALCHAIN_SUBMITTER_BACKEND=mock` | No | `LABMOCK-<sha256…>` |
| **outbox** | `TEGALCHAIN_SUBMITTER_BACKEND=outbox` | No | *(none — JSON outbox only)* |
| **cosmos** | `TEGALCHAIN_SUBMITTER_BACKEND=cosmos` | Yes — Cosmos REST | `txhash` from module |
| **qortal** (legacy) | `TEGALCHAIN_SUBMITTER_BACKEND=qortal` + `TEGALCHAIN_PRIVKEY` | Yes — Qortal :12391 | Qortal signature |

Auto-resolution when `TEGALCHAIN_SUBMITTER_BACKEND` is unset:

1. Explicit `TEGALCHAIN_SUBMITTER_BACKEND`
2. `TEGALCHAIN_LAB_MOCK_SUBMIT=1` → mock
3. `TEGALCHAIN_COSMOS_REST_URL` set → cosmos
4. `TEGALCHAIN_PRIVKEY` set → qortal
5. Else → outbox

## Quick start (Replit Shell — no Qortal)

```bash
cd ~/sovereign-ecosystem
pip install -r requirements.txt

# Terminal 1 — mint worker
export TEGALCHAIN_IDENTITY_MODE=dev
python -m integrations.mint_worker

# Terminal 2 — ingest + mock drain
export MINT_WORKER_URL=http://127.0.0.1:8090
python integrations/zeegate_telemetry/client.py

export TEGALCHAIN_SUBMITTER_BACKEND=mock   # default in replit-mint-drain.sh
bash scripts/replit-mint-drain.sh 5
python -m tegalchain.submitter stats
```

**Success:** `"submitted": 1`, `"outboxed": 0`, `submit_ref` starts with `LABMOCK-`.

Re-drain existing outboxed rows: mock backend processes `pending` **and** `outboxed` queue rows.

Verify GTR + Auditrail + GreenLedger (path is **`/records/`** plural, not `/record/`):

```bash
curl -s "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | python -m json.tool
```

Expect `status: submitted`, `ledger_ref` (`LABMOCK-…`), `on_chain_anchor.anchor_timestamp`, `auditrail.submit_ref`, and `greenledger_entry`.

## MQTT v5 ingest (optional)

With a broker on `:1883` (e.g. Mosquitto on Replit or local):

```bash
# Terminal 1 — REST + embedded MQTT bridge
export MINT_WORKER_MQTT_ENABLED=1
export MINT_WORKER_MQTT_BROKER=127.0.0.1
export TEGALCHAIN_MINT_QUEUE_DB=tegalchain/data/mint_queue.db
python -m integrations.mint_worker
```

Publish a signed GTR JSON to `gtp/{source_id}/readings`; subscribe to `gtp/{source_id}/ack` for `{gtr_id, queue_id, status, ledger_ref}`. Errors publish on `gtp/{source_id}/errors`. Topic `source_id` must match the payload `source_id` / `node_id`.

## Continuous watch

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=mock
./scripts/replit-mint-watch.sh 20 30
```

## Cosmos REST backend (when devnet is ready)

Point at a Greenledger anchor module (future `x/auditrail` / gretelemetry handler):

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=cosmos
export TEGALCHAIN_COSMOS_REST_URL=http://localhost:1317
export TEGALCHAIN_COSMOS_ANCHOR_PATH=/tegalchain/gretelemetry/v1/anchor
python -m tegalchain.submitter drain --limit 5
```

POST body: `{ "type": "TELEMETRY_MINT", "block_candidate": …, "on_chain_anchor": … }`  
Expected response: `{ "txhash": "…" }` (or `submit_ref` / `ledger_ref`).

## Legacy Qortal (optional)

Only if you intentionally run a Qortal node:

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=qortal
export TEGALCHAIN_PRIVKEY=...
export TEGALCHAIN_API_URL=http://127.0.0.1:12391
python -m tegalchain.submitter drain
```

## Success criteria (lab / Replit)

Verified on Replit **2026-07-27** (Phase 1 client ingest — `gtr_id`: `7542b54e-457e-4416-904d-abf570529d5a`, `ledger_ref`: `LABMOCK-5495E57D4B5AAE1271BCC84A5063A8A3FAC9FA91-Q000002`).

Verified on Replit **2026-07-28** (Phase 2 CDR fixture — `gtr_id`: `8717180f-9e32-4d5a-9099-8ccf08ee75ea`, `ledger_ref`: `LABMOCK-CCDC9378EFD230D6571ACF754E083F088895E822-Q000003`). See [PHASE-2.md](../phases/PHASE-2.md).

Verified on Replit **2026-07-29** (Phase 7 staging — tegalid + Bearer → GLE + Carbon Account — `gtr_id`: `bd1a476b-a8a1-4edc-89b9-50b205adf72f`, `source_id`: `did:tegal:LABEDGE001`). See [PHASE-7.md](../phases/PHASE-7.md) and `./scripts/replit-sync-check.sh`.

- [x] Mint worker accepts GTR (`POST /v1/telemetry/records`, MQTT `gtp/{source_id}/readings`, or legacy client)
- [x] Drain with **mock** → `submitted` + `LABMOCK-…` ref
- [x] `GET /v1/telemetry/records/{gtr_id}` → `ledger_ref`, `auditrail`, `greenledger_entry`
- [x] `sla-check` → `violation_count: 0` under normal load
- [x] Outbox JSON still written under `tegalchain/data/outbox/` (audit copy)

## Related

- [PHASE-1.md](../phases/PHASE-1.md)
- [PHASE-2.md](../phases/PHASE-2.md) — CDR fixture → drain → `ledger_ref`
- [scripts/zeegate-cdr-watch.sh](../../scripts/zeegate-cdr-watch.sh) — optional live Docker CDR ingest
- [scripts/replit-sync-check.sh](../../scripts/replit-sync-check.sh) — verify git pull + Phase 7 scripts on Replit
- [TP-101-GREENTELEMETRY.md](../standards/TP-101-GREENTELEMETRY.md)
