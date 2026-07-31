# Phase 2 — Zeegate cloud voice

**Status:** Complete (lab profile) — Replit fixture CDR → `ledger_ref` verified 2026-07-28  
**Depends on:** Phase 1 mint pipeline operational.

## Scope

| Component | Status |
|-----------|--------|
| `zeegate-cloud/kamailio/` | Done — SBC/registrar, edge auth, FS dispatch |
| `zeegate-cloud/freeswitch/` | Done — lab dialplan, external profile, CSV CDR |
| `zeegate-cloud/deploy/` | Done — docker-compose lab stack |
| *(removed orchestration adapter)* | **Removed** — tegalid + server-side SIP provisioning only |
| `zeegate-cloud/cdr_adapter/` | **Live** — CDR CSV → adapter-normalized GTR → mint worker |

## Architecture

```text
Zeegate gsm2sip ──REGISTER──► Kamailio :5060 (zeegate.lab)
                                    │
                    4-digit ext ────┼──► FreeSWITCH :5080 (echo/bridge)
                    edge001 ────────┘    CDR → zeegate_cdr volume
```

## Run lab stack

```bash
cd zeegate-cloud/deploy
cp .env.example .env
./up.sh
```

### Lab accounts

| User | Password | Use |
|------|----------|-----|
| `edge001` | `edge001` | Zeegate PJSIP registration |
| `lab1000` | `lab1000` | Softphone test client |

### Test call path

1. Register softphone as `lab1000@zeegate.lab`
2. Dial **1000** → Kamailio → FreeSWITCH echo
3. Register Zeegate as `edge001` → dial **3000** to bridge

## Exit criteria

- [x] Lab SIP call through Kamailio → FreeSWITCH
- [x] CDR adapter code path (CSV → GTR → mint worker; tegalid `sip_user` resolution)
- [x] Live lab: CDR → adapter → submitted `ledger_ref` on Replit (fixture path; mock drain)

Verified on Replit **2026-07-28** (example `gtr_id`: `8717180f-9e32-4d5a-9099-8ccf08ee75ea`, `ledger_ref`: `LABMOCK-CCDC9378EFD230D6571ACF754E083F088895E822-Q000003`).

### Replit fixture path (no live SIP required)

```bash
# Shell 1 — mint worker (after git pull ≥ 5f6c9f5 for dev-mode CDR attestations)
export TEGALCHAIN_IDENTITY_MODE=dev
export TEGALCHAIN_MINT_QUEUE_DB=tegalchain/data/mint_queue.db
python3 -m integrations.mint_worker

# Shell 2 — fixture CDR → adapter → drain → verify
mkdir -p /tmp/zeegate-cdr
cp zeegate-cloud/cdr_adapter/fixtures/sample_cdr.csv /tmp/zeegate-cdr/Master.csv
export ZEEGATE_CDR_DIR=/tmp/zeegate-cdr
export MINT_WORKER_URL=http://127.0.0.1:8090
PYTHONPATH=zeegate-cloud python3 -m cdr_adapter once
bash scripts/replit-mint-drain.sh 5
curl -s "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | python3 -m json.tool
```

Expect `status: submitted`, `ledger_ref` (`LABMOCK-…`), `auditrail`, `greenledger_entry`, and CDR metadata (`evidence_kind: CDR`, `call_id_hash`).

## Related

| Doc / script | Use |
|--------------|-----|
| [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md) | Mock drain, SLA check, verify `ledger_ref` / GLE after ingest |
| [zeegate-cloud/cdr_adapter/README.md](../../zeegate-cloud/cdr_adapter/README.md) | CDR adapter env vars, fixture vs live volume |
| [scripts/zeegate-cdr-watch.sh](../../scripts/zeegate-cdr-watch.sh) | **Optional** — watch FreeSWITCH `zeegate_cdr` Docker volume after `./up.sh` |
| [zeegate-cloud/deploy/README.md](../../zeegate-cloud/deploy/README.md) | Kamailio + FreeSWITCH `./up.sh` lab stack |
| [zeegate-cloud/README.md](../../zeegate-cloud/README.md) | Phase 2 voice cloud overview |
| [zeegate/README.md](../../zeegate/README.md) | Android DePIN edge (gsm2sip) |

**Live Docker CDR (optional):** bring up the voice stack (`cd zeegate-cloud/deploy && ./up.sh`), place or mount CDR CSV under `zeegate_cdr`, run `./scripts/zeegate-cdr-watch.sh once`, then drain per [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md).

## Next

Continue at [phases/README.md](./README.md):

1. **[Phase 3 — Live voice CDR](./PHASE-3.md)** — real hangup CSV from `zeegate_cdr` volume (current focus)
2. **[Phase 4 — DePIN edge producers](./PHASE-4.md)** — Zeegate Android + Bytenergy
3. **[Phase 5 — Cosmos devnet anchor](./PHASE-5.md)** — replace mock with `txhash`
