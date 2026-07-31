# Zeegate cloud lab deployment

Docker Compose stack for Phase 2 voice path:

```text
Zeegate gsm2sip  ──REGISTER──►  Kamailio :5060  ──INVITE──►  FreeSWITCH :5080
Lab softphone    ──REGISTER──►  (zeegate.lab)              (echo / bridge / CDR)
```

## Prerequisites

- Docker Engine + Compose v2
- UDP **5060** (SIP) and **16384–16394** (RTP) reachable from Zeegate device or emulator network
- Kamailio image pulls from **ghcr.io** (`ghcr.io/kamailio/kamailio`) — official images moved off Docker Hub

## Start

```bash
cd zeegate-cloud/deploy
cp .env.example .env    # optional port overrides
./up.sh
```

Or manually:

```bash
docker compose up -d
docker compose logs -f kamailio freeswitch
```

## Lab test (softphone)

1. Register as `lab1000@zeegate.lab` / password `lab1000` to `<host-ip>:5060`
2. Dial **1000** — echo via FreeSWITCH
3. Register Zeegate as `edge001@zeegate.lab` / `edge001`
4. Dial **3000** from softphone — bridges to edge

## Zeegate edge

```kotlin
// MainActivity — point at lab Kamailio
initPjsip("<host-ip>", "edge001", "edge001")
```

Ensure Android can reach host UDP 5060 (emulator: use host LAN IP, not `10.0.2.2`, for SIP unless port-forwarded).

## CDR → mint pipeline

Hangup CSV files land in Docker volume `zeegate_cdr`:

```bash
docker run --rm -v zeegate_cdr:/cdr alpine ls -la /cdr
```

Process with the CDR adapter (mount or copy volume path to `ZEEGATE_CDR_DIR`):

```bash
export ZEEGATE_CDR_DIR=/path/to/cdr-mount
export MINT_WORKER_URL=http://127.0.0.1:8090
../../scripts/zeegate-cdr-watch.sh once
```

See [cdr_adapter/README.md](../cdr_adapter/README.md).

## Stop

```bash
docker compose down
```

## Troubleshooting

### Kamailio restart loop — `could not find module <dbtext>`

The ghcr.io image is module-minimal. Compose **builds** `Dockerfile.kamailio` to copy `db_text.so` (and peers) from the official `kamailio` deb on `deb-archive.kamailio.org`. Rebuild:

```bash
docker compose build kamailio
docker compose up -d --force-recreate kamailio
docker compose logs --tail=20 kamailio
```

### FreeSWITCH `fs_cli` — `Error Connecting []`

The stock image binds ESL on `::`, which fails on Replit/Docker without global IPv6. Compose mounts `event_socket.conf.xml` with `listen-ip=127.0.0.1`. After `git pull`:

```bash
cd zeegate-cloud/deploy
docker compose up -d --force-recreate freeswitch
docker exec zeegate-freeswitch fs_cli -H 127.0.0.1 -P 8021 -p ClueCon -x status
```

### FreeSWITCH `unhealthy` / IPv6 sofia errors

IPv6 profile bind failures are common in Docker and often non-fatal for lab **IPv4** on `:5080`. For CDR without an external softphone:

```bash
cd ~/workspace/sovereign-ecosystem
./scripts/phase3-fs-lab-call.sh
./scripts/phase3-live-cdr.sh drain
```

### Empty `zeegate_cdr` volume

CDR CSV appears only after a **completed call**. Place a softphone call or use `phase3-fs-lab-call.sh` above.
