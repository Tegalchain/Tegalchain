# Phase 7 — staging soak runbook

Continuous drain + anchor SLA monitoring for production/staging profile.

## Prerequisites

```bash
cd ~/workspace/sovereign-ecosystem
git pull origin main

export MINT_WORKER_BEARER_TOKEN=<secret>   # openssl rand -hex 24
./scripts/restart-mint-worker-prod.sh      # Shell 1 — leave running
```

Producers (CDR adapter, edge clients) must send:

```http
Authorization: Bearer <MINT_WORKER_BEARER_TOKEN>
```

## One-shot verify

```bash
export MINT_WORKER_BEARER_TOKEN=<same-secret>
./scripts/phase7-verify-staging.sh staging
```

## 24h soak (Shell 2)

Start the soak watch (writes JSONL audit log, integrity each cycle):

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=mock   # or cosmos
./scripts/phase7-soak-watch.sh 20 30
```

Default log: `tegalchain/data/soak_watch.log`. Override with `PHASE7_SOAK_LOG`.

The script prints **started** and **target end** timestamps (24h from start). Leave running until target end or stop with Ctrl+C after 24h.

Lab shortcut (1h span for verify):

```bash
REPLIT_SOAK_HOURS=1 ./scripts/phase7-soak-watch.sh 20 30
```

During soak you may run staging ingest (optional proof GTR):

```bash
export MINT_WORKER_BEARER_TOKEN=<same-secret>
./scripts/phase7-staging-ingest.sh
```

## Mark soak complete

After at least 24h (or `REPLIT_SOAK_HOURS` in lab):

```bash
export MINT_WORKER_BEARER_TOKEN=<same-secret>   # optional but recommended
./scripts/phase7-soak-verify.sh
```

Verify checks:

- Soak log exists and span ≥ 24h (or `REPLIT_SOAK_HOURS`)
- No cycle with `sla.violation_count > 0` or `integrity.violation_count > 0`
- At least one integrity cycle in the log
- If `MINT_WORKER_BEARER_TOKEN` is set: runs `./scripts/phase7-verify-staging.sh staging`

Exit `0` prints `OK:` summary; exit `1` prints `FAIL:` reason.

Update [PHASE-7.md](../phases/PHASE-7.md) exit criteria when verify passes.

## Continuous watch (manual, no soak log)

```bash
export TEGALCHAIN_SUBMITTER_BACKEND=mock   # or cosmos
PHASE7_INTEGRITY=1 ./scripts/replit-mint-watch.sh 20 30
# with JSONL log:
PHASE7_INTEGRITY=1 ./scripts/replit-mint-watch.sh --log tegalchain/data/soak_watch.log 20 30
```

Each cycle drains pending rows and reports anchor SLA. With `PHASE7_INTEGRITY=1`, also runs `integrity-check --schedule DAILY`. Exit code `2` when `violation_count > 0` (SLA or integrity).

## Alert condition

```bash
curl -s -H "Authorization: Bearer $MINT_WORKER_BEARER_TOKEN" \
  http://127.0.0.1:8090/v1/queue/anchor-sla | python3 -m json.tool
```

Alert when `violation_count > 0`.

## Scheduled integrity (cron / Replit scheduled task)

```bash
python3 -m tegalchain.greenledger integrity-check --schedule DAILY
```

Exit code `2` on violations (persisted to `greenledger_integrity_violations`).

## Cold-tier export (weekly job)

```bash
python3 -m tegalchain.greenledger export-cold --output-dir tegalchain/data/cold_export
```

Upload resulting `gle_cold_export_*.jsonl` to object storage in production.

## 24h soak exit criteria

- [ ] `./scripts/phase7-soak-watch.sh` runs without SLA/integrity exit code 2 for 24h
- [ ] `./scripts/phase7-soak-verify.sh` passes (log span, zero violations, integrity cycles)
- [ ] `./scripts/phase7-verify-staging.sh staging` passes after at least one drain (included when bearer token set)

## Related

- [PHASE-7.md](../phases/PHASE-7.md)
- [LAB-MINT-DRAIN.md](./LAB-MINT-DRAIN.md)
