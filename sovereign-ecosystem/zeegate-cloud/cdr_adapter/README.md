# Zeegate CDR adapter

Phase 2 **adapter-normalized CDR** → TP-101 GTR → mint worker (same oracle path as Phase 1).

Raw FreeSWITCH CSV stays in the voice subsystem; the adapter publishes **public summaries only** (`bytes`, duration, `call_id_hash`) per [GREETELEMETRY-ORACLE-BOUNDARY.md](../../docs/contracts/GREETELEMETRY-ORACLE-BOUNDARY.md).

## Flow

```text
FreeSWITCH hangup → CDR CSV (zeegate_cdr volume)
        → cdr_adapter (normalize + Ed25519 GTR)
        → POST /v1/telemetry/records (mint worker)
        → mint queue → submitter → Tegalchain anchor
```

## SIP extension → tegalid

Lab `sip_user` values (e.g. `edge001`) resolve via [tegalid_bindings.example.json](../../tegalchain/data/tegalid_bindings.example.json) to `did:tegal:…` for tegalid-gated mint.

## Run once (lab)

```bash
# Copy sample CDR into a watch directory
mkdir -p /tmp/zeegate-cdr
cp zeegate-cloud/cdr_adapter/fixtures/sample_cdr.csv /tmp/zeegate-cdr/Master.csv

export ZEEGATE_CDR_DIR=/tmp/zeegate-cdr
export MINT_WORKER_URL=http://127.0.0.1:8090   # optional — omit for build-only

PYTHONPATH=zeegate-cloud python -m cdr_adapter once
```

## Watch loop (with Docker CDR volume)

After `./up.sh` and test calls:

```bash
docker run --rm -v zeegate_cdr:/cdr:ro alpine ls -la /cdr

export ZEEGATE_CDR_DIR=/path/to/mounted/cdr
export MINT_WORKER_URL=http://127.0.0.1:8090
./scripts/zeegate-cdr-watch.sh once
```

Continuous:

```bash
./scripts/zeegate-cdr-watch.sh watch 15 4   # 4 cycles, 15s interval
```

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `ZEEGATE_CDR_DIR` | `/var/log/freeswitch/cdr-csv` | FreeSWITCH CSV directory |
| `ZEEGATE_CDR_STATE_DB` | `tegalchain/data/cdr_watcher.db` | Processed UUID dedupe |
| `MINT_WORKER_URL` | — | Mint worker base URL |
| `MINT_WORKER_BEARER_TOKEN` | — | REST Bearer auth |
| `ZEEGATE_CDR_FALLBACK_SOURCE` | `edge001` | Source when bindings file missing |

## Related

- [PHASE-2.md](../../docs/phases/PHASE-2.md) — exit criteria and Replit fixture path
- [LAB-MINT-DRAIN.md](../../docs/runbooks/LAB-MINT-DRAIN.md) — mock drain after adapter ingest
- [scripts/zeegate-cdr-watch.sh](../../scripts/zeegate-cdr-watch.sh) — optional live Docker CDR volume watch

## Tests

```bash
PYTHONPATH=zeegate-cloud python -m unittest discover -s zeegate-cloud/cdr_adapter -p 'test_*.py' -v
```
