# Phase 3 — Live voice CDR (Docker)

**Status:** **Complete** (lab profile, Replit 2026-07-28)  
**Depends on:** [PHASE-2.md](./PHASE-2.md) complete (lab profile); Phase 1 mint worker + mock drain  
**Goal:** Prove **live** FreeSWITCH CDR from the Docker voice stack → adapter → mint queue → **`LABMOCK-…` `ledger_ref`**  
**Stack:** Phase 2 voice + [TP-101](../standards/TP-101-GREENTELEMETRY.md) CDR GTR + [TP-103](../standards/TP-103-GREENLEDGER.md) GLE (mock anchor)

Phase 2 closed the **fixture** path (`sample_cdr.csv` → `/tmp/zeegate-cdr`). Phase 3 closed the **operational** path: internal FS originate (or SIP call) → CSV in volume `zeegate_cdr` → adapter ingest → mock drain.

## Closure (Replit lab)

| Proof | Value |
|-------|--------|
| Live CDR `gtr_id` (example) | `e9e4bc8f-c775-454d-b389-073df66887ad` |
| Adapter ingest | `processed_rows: 3` from `Master.csv` |
| Mock drain | `submitted: 2` (telemetry_hash dedupe on loopback echo rows) |
| Queue total submitted | `5` (Phases 1–3 combined) |
| Phase 2 fixture (distinct) | `8717180f-9e32-4d5a-9099-8ccf08ee75ea` |

Fixes landed on `main`: Kamailio `db_text` Docker build (`cd17d3b`), registrar PV check (`683085c`), FreeSWITCH ESL `127.0.0.1` (`8ec7db0`), CDR sync permissions (`cddc5bb`), empty byte counters parse (`0d1ad7d`).

## Scope

| Component | Status |
|-----------|--------|
| `zeegate-cloud/deploy/` `./up.sh` | Done |
| Docker volume `zeegate_cdr` | Done — FreeSWITCH CSV sink |
| `scripts/phase3-live-cdr.sh` | Done — sync + ingest + drain |
| `scripts/phase3-fs-lab-call.sh` | Done — internal originate (no softphone) |
| Live CDR → `LABMOCK-…` | **Verified** |

## Architecture

```text
lab1000 / edge001 ──SIP──► Kamailio ──► FreeSWITCH hangup
       or fs_cli originate (phase3-fs-lab-call.sh)
                                              │
                                              ▼
                                    zeegate_cdr volume (*.csv)
                                              │
                                              ▼
                              cdr_adapter / phase3-live-cdr.sh
                                              │
                                              ▼
                                    mint worker :8090 → queue → mock drain
```

## Run (reference)

### Shell 1 — mint worker

```bash
./scripts/start-mint-worker.sh
```

### Shell 2 — voice + CDR

```bash
cd zeegate-cloud/deploy && docker compose up -d
./scripts/phase3-fs-lab-call.sh
./scripts/phase3-live-cdr.sh drain
```

### Verify

```bash
curl -s "http://127.0.0.1:8090/v1/telemetry/records/e9e4bc8f-c775-454d-b389-073df66887ad" | python3 -m json.tool
curl -s http://127.0.0.1:8090/v1/queue/stats | python3 -m json.tool
```

## Exit criteria

- [x] Docker voice stack up (FreeSWITCH ESL + Kamailio registrar)
- [x] Lab call completes (`phase3-fs-lab-call.sh` → `+OK` UUID)
- [x] CDR CSV in `zeegate_cdr` (`Master.csv`)
- [x] `phase3-live-cdr.sh drain` → `processed_rows ≥ 1`, new `gtr_id`
- [x] Mock drain → `submitted ≥ 1`, `ledger_ref` starts with `LABMOCK-`
- [x] `GET /v1/telemetry/records/{gtr_id}` → `evidence_kind: CDR`, GLE + auditrail

## Notes

- **Replit:** UDP SIP/RTP may be blocked — use `phase3-fs-lab-call.sh` for CDR without softphone.
- **Dedupe:** Mint queue dedupes by `telemetry_hash`; identical loopback echo rows share a queue id.
- **Zeegate Android:** register `edge001` against host Kamailio — see [Phase 4](./PHASE-4.md).

## Related

- [PHASE-4.md](./PHASE-4.md) — **next:** edge producers
- [PHASE-2.md](./PHASE-2.md) — fixture path
- [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md)
- [zeegate-cloud/deploy/README.md](../../zeegate-cloud/deploy/README.md)

## Next

[Phase 4 — DePIN edge producers](./PHASE-4.md): Zeegate `TelemetryService`, Python sim, and Bytenergy client POST directly to the mint worker.
