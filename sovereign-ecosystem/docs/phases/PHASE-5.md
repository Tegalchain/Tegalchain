# Phase 5 — Cosmos devnet anchor

**Status:** **Complete** (lab profile, Replit 2026-07-28) — real devnet remains target  
**Depends on:** Phases 1–4 complete (lab); at least one producer path proven  
**Goal:** Submit anchored GTRs via **Cosmos REST** — `ledger_ref` = **`txhash`**, not `LABMOCK-…`  
**Stack:** Phase 1 submitter + [TP-103](../standards/TP-103-GREENLEDGER.md) GLE + `tegalchain-core` devnet (target)

Lab mock (`TEGALCHAIN_SUBMITTER_BACKEND=mock`) proves pipeline logic. Phase 5 proves **ledger integration**: the same mint queue drains through the Cosmos submitter path.

## Closure (Replit lab)

Verified **2026-07-28** via `./scripts/phase5-cosmos-drain.sh ingest` + `verify`:

| Proof | Value |
|-------|--------|
| `gtr_id` | `5ed46400-89be-4d65-91e8-2a809b1f1b15` |
| `ledger_ref` | `15171889E76259444F2DD323E87B9BFABC925352A17EA7751FC487A1B34A168A` |
| `status` | `submitted` |
| Backend | `cosmos` via `integrations/cosmos_anchor_lab` on `:1317` |

Distinct from Phase 4 mock ref (e.g. `LABMOCK-1E033317…-Q000007`). Implementation landed in **`63db7ce`**.

## Scope

| Component | Status |
|-----------|--------|
| `tegalchain/submitter/cosmos.py` | Done — REST POST client |
| `integrations/cosmos_anchor_lab/` | Done — lab stub on `:1317` (Replit/WSL) |
| `tegalchain-core` Cosmos devnet | **Target** — replace lab stub with real node |
| `x/auditrail` / gretelemetry module | **Target** in chain |

## Architecture

```text
mint queue (pending GTR)
        │
        ▼
tegalchain.submitter drain  (backend=cosmos)
        │
        ▼
POST /tegalchain/gretelemetry/v1/anchor  →  txhash
        │
        ▼
GLE + auditrail correlation (ledger_ref = txhash)
```

## Prerequisites

- Mint worker running (`./scripts/start-mint-worker.sh`).
- Python deps installed (`pip install -r requirements.txt`).
- **New pending row** in queue (Phase 4 rows are already `LABMOCK-` submitted — ingest again for Phase 5).

---

## Run — Lab stub (Replit / WSL)

Three shells:

### Shell 1 — mint worker

```bash
cd ~/workspace/sovereign-ecosystem
./scripts/start-mint-worker.sh
```

### Shell 2 — Cosmos anchor lab (stub devnet)

```bash
cd ~/workspace/sovereign-ecosystem
./scripts/start-cosmos-anchor-lab.sh
```

Confirm:

```bash
curl -s http://127.0.0.1:1317/health | python3 -m json.tool
```

### Shell 3 — ingest + cosmos drain

**One-shot helper:**

```bash
cd ~/workspace/sovereign-ecosystem
chmod +x scripts/phase5-cosmos-drain.sh
./scripts/phase5-cosmos-drain.sh ingest
```

This POSTs one Zeegate row, drains with `backend=cosmos`, and prints queue stats.

**Verify** (use `gtr_id` from ingest output):

```bash
./scripts/phase5-cosmos-drain.sh verify <gtr_id>
```

Or manually:

```bash
curl -s "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | python3 -m json.tool | \
  grep -E '"status"|ledger_ref'
```

Expect:

- `"status": "submitted"`
- `"ledger_ref": "<64-char hex>"` — **not** `LABMOCK-…`

---

## Manual path

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=cosmos
export TEGALCHAIN_COSMOS_REST_URL=http://127.0.0.1:1317
export TEGALCHAIN_COSMOS_ANCHOR_PATH=/tegalchain/gretelemetry/v1/anchor
export MINT_WORKER_URL=http://127.0.0.1:8090

python3 integrations/zeegate_telemetry/client.py
python3 -m tegalchain.submitter drain --limit 5
python3 -m tegalchain.submitter stats
```

POST body to anchor module:

```json
{
  "type": "TELEMETRY_MINT",
  "block_candidate": { "...": "..." },
  "on_chain_anchor": { "...": "..." }
}
```

Expected response: `{ "txhash": "…" }`.

---

## Run — Real devnet (when ready)

1. Run Tegalchain devnet from `tegalchain-core/` (Cosmos REST on `:1317`).
2. Deploy or enable gretelemetry anchor module route (same path or update `TEGALCHAIN_COSMOS_ANCHOR_PATH`).
3. Stop the lab stub; point `TEGALCHAIN_COSMOS_REST_URL` at the devnet.
4. Ingest + `./scripts/phase5-cosmos-drain.sh ingest`.
5. Query chain for anchor tx; verify `GET /v1/telemetry/records/{gtr_id}`.

See [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md#cosmos-rest-backend-when-devnet-is-ready).

---

## Exit criteria

- [x] Cosmos anchor reachable (`/health` on lab stub)
- [x] At least one **new** queue row drains with `backend: cosmos`
- [x] `ledger_ref` is 64-char hex `txhash` (not `LABMOCK-` prefix)
- [x] `GET /v1/telemetry/records/{gtr_id}` — `status: submitted`
- [ ] (Target) Anchor queryable on real devnet module / CLI

## Rollback

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=mock
bash scripts/replit-mint-drain.sh 10
```

Mock drain continues to work for CI and Replit free tier.

## Related

- [PHASE-4.md](./PHASE-4.md) — edge producers (complete Track A)
- [TEGALCHAIN.md](../TEGALCHAIN.md)
- [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md)
- [scripts/phase5-cosmos-drain.sh](../../scripts/phase5-cosmos-drain.sh)
- [scripts/start-cosmos-anchor-lab.sh](../../scripts/start-cosmos-anchor-lab.sh)

## Next

[Phase 6 — TP-102 Proof of Resonance](./PHASE-6.md): score verified GTRs before or after anchor.
