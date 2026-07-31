# Zeegate cloud voice stack

Phase 2 lab stack for sovereign DePIN telecom: **Kamailio** (SBC/registrar) + **FreeSWITCH** (media/CDR).

```text
tegalid-gated SIP credentials (server-side) → Kamailio → FreeSWITCH → Zeegate gsm2sip edge
                                                      └── CDR CSV → cdr_adapter → mint worker
```

| Directory | Role |
|-----------|------|
| `kamailio/` | SIP registrar / SBC — edge registration, dispatch to media |
| `freeswitch/` | Echo, tone, bridge dialplan + CSV CDR |
| `cdr_adapter/` | CDR CSV → TP-101 GTR → mint worker |
| `deploy/` | Docker Compose lab stack |

**Not in scope:** No cloud orchestration adapter in this stack. Identity and mint eligibility use **tegalid** on the Greenledger; SIP lab accounts are provisioned server-side (Kamailio `dbtext` + bindings).

## Quick start

```bash
cd zeegate-cloud/deploy
./up.sh
```

See [deploy/README.md](deploy/README.md) for softphone lab tests and Zeegate `initPjsip` settings.

## Docs

- [docs/phases/PHASE-2.md](../docs/phases/PHASE-2.md) — scope and exit criteria
- [kamailio/README.md](kamailio/README.md) — lab SIP accounts
- [freeswitch/README.md](freeswitch/README.md) — extensions and CDR

## Mint pipeline

FreeSWITCH CDR CSV → [cdr_adapter/](cdr_adapter/) (adapter-normalized GTR) → Phase 1 mint worker → mint queue → Tegalchain anchor.

```bash
export MINT_WORKER_URL=http://127.0.0.1:8090
../../scripts/zeegate-cdr-watch.sh once
```
