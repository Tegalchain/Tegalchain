# Zeegate lab SIP accounts (domain `zeegate.lab`)

| User | Password | Role |
|------|----------|------|
| `edge001` | `edge001` | Zeegate gsm2sip edge registration |
| `lab1000` | `lab1000` | Lab softphone / test client |

HA1 (for external provisioning tools):

- `edge001` → `5e67d6d7a14f264433015b444ac98355`
- `lab1000` → `1baa5307865dd959b207b5591667eb4b`

## Zeegate / PJSIP

Point `initPjsip(server, user, pass)` at the host running docker-compose:

```kotlin
initPjsip("192.168.x.x", "edge001", "edge001")
```

SIP URI: `sip:edge001@zeegate.lab`

## Routing

| Destination | Path |
|-------------|------|
| `1000` | Kamailio → FreeSWITCH echo |
| `2000` | Kamailio → FreeSWITCH tone stream |
| `3000` | Kamailio → bridge to registered `edge001` |
| `edge001` | Kamailio usrloc → Zeegate edge |

Configs: `kamailio.cfg`, `dispatcher.list`, `dbtext/subscriber`.
