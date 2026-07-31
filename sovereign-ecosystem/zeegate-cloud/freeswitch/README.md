# FreeSWITCH — Zeegate lab media server

Kamailio forwards 4-digit lab extensions to this node (`freeswitch:5080`).

## Lab extensions

| Extension | Application |
|-----------|-------------|
| `1000` | Echo test |
| `2000` | Tone stream |
| `3000` | Bridge to `edge001@kamailio` (registered Zeegate edge) |
| `3xxx` | Welcome IVR fallback |

## CDR

`mod_cdr_csv` writes hangup records to `/var/log/freeswitch/cdr-csv/` inside the container (docker volume `zeegate_cdr`). Fields include duration and read/write byte counters for greentelemetry aggregation via [cdr_adapter/](../cdr_adapter/).

## Layout

```
freeswitch/
├── dialplan/public/00_zeegate_lab.xml
├── sip_profiles/external.xml
└── autoload_configs/
    ├── cdr_csv.conf.xml
    └── event_socket.conf.xml   # 127.0.0.1 ESL for fs_cli in Docker/Replit
```

The `safarov/freeswitch` image loads stock config; compose mounts these files over the defaults listed in `deploy/docker-compose.yml`.
