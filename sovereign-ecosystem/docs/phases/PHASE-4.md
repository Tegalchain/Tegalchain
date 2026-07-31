# Phase 4 — DePIN edge producers

**Status:** Complete (Track A lab, Replit 2026-07-28) — Track B (Android) optional  
**Depends on:** [PHASE-1.md](./PHASE-1.md) mint worker + mock drain; Phase 3 recommended (voice + `edge001` binding context)  
**Goal:** **Edge nodes** publish signed gretelemetry to the same oracle as cloud CDR → **`LABMOCK-…` `ledger_ref`**  
**Stack:** [TP-107](../PROTOCOL-STACK.md#tp-107--sovereign-platforms) → [TP-101](../standards/TP-101-GREENTELEMETRY.md) → Phase 1 mint pipeline

Phase 1 proved Python lab clients; Phase 2–3 proved CDR adapter paths. Phase 4 proves **subsystem-native producers** at the edge without coupling Tegalchain to Android or meter internals ([oracle boundary](../contracts/GREETELEMETRY-ORACLE-BOUNDARY.md)).

## Scope

| Producer | Location | Metric (v1) | Lab track |
|----------|----------|-------------|-----------|
| Zeegate Python sim | `integrations/zeegate_telemetry/` | `telecom_bandwidth_bytes` | **A — Replit/WSL first** |
| Bytenergy utility | `bytenergy-utility/` | `energy_generation_kwh` | **A — Replit/WSL first** |
| Zeegate Android | `zeegate/app/` | same (legacy HMAC envelope) | **B — emulator/device** |
| MQTT v5 (optional) | `integrations/mint_worker/mqtt_bridge.py` | GTR JSON | **C — optional** |

## Architecture

```text
Zeegate Android (TelemetryService)  ──POST /v1/telemetry──► mint worker :8090
integrations/zeegate_telemetry        ──POST────────────────►       │
bytenergy-utility/client.py           ──POST────────────────►       │
MQTT gtp/{source_id}/readings         ──MQTT────────────────►       │
                                                                    ▼
                                                          queue → mock drain → GLE
```

## Prerequisites

- Phase 3 complete (live Docker CDR path verified on lab).
- Mint worker running in **dev** mode (`TEGALCHAIN_IDENTITY_MODE=dev`).
- Python deps: `pip install -r requirements.txt` (if not already).

## Run — Track A (Python sim, Replit or WSL)

Fastest path — no Android Studio required. Proves the same oracle ingress Android will use.

### Shell 1 — mint worker

```bash
cd ~/workspace/sovereign-ecosystem   # Replit
# cd ~/sovereign-ecosystem           # WSL
./scripts/start-mint-worker.sh
```

Confirm:

```bash
curl -s http://127.0.0.1:8090/health | python3 -m json.tool
```

### Shell 2 — edge producers + drain

**Helper (both producers + drain + stats):**

```bash
cd ~/workspace/sovereign-ecosystem
chmod +x scripts/phase4-edge-telemetry.sh
./scripts/phase4-edge-telemetry.sh both
```

**Or step by step:**

```bash
export MINT_WORKER_URL=http://127.0.0.1:8090

# Zeegate telecom bandwidth (legacy envelope, dev HMAC key)
python3 integrations/zeegate_telemetry/client.py

# Bytenergy prosumer energy (legacy envelope)
python3 bytenergy-utility/client.py

bash scripts/replit-mint-drain.sh 10
curl -s http://127.0.0.1:8090/v1/queue/stats | python3 -m json.tool
```

Each POST should return JSON with `gtr_id`, `queue_id`, and `status: pending` (before drain) or `submitted` (after drain if you query again).

### Verify records

Use the `gtr_id` from the POST response (there is no list endpoint):

```bash
curl -s "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | python3 -m json.tool
```

**Zeegate sim** — expect:

- `metadata.system_type` or legacy `system_type`: `ZEEGATE_TELECOM`
- `node_id`: `zerocell-node-001` (legacy path)
- After drain: `status: submitted`, `ledger_ref` starts with `LABMOCK-`

**Bytenergy** — expect:

- `system_type`: `BYTENERGY_UTILITY`
- `node_id`: `bytenergy-prosumer-001`
- `metrics.energy_generation_kwh` present on legacy envelope

Distinct from Phase 3 CDR records (`evidence_kind: CDR`, `adapter: zeegate_cdr`).

---

## Run — Track B (Zeegate Android)

Proves the on-device `TelemetryService` → `MintWorkerClient` path.

### 1. Host setup (WSL recommended)

```bash
cd ~/sovereign-ecosystem
./scripts/start-mint-worker.sh
cd zeegate-cloud/deploy && docker compose up -d   # Kamailio + FreeSWITCH for SIP leg
```

Note your **host LAN IP** (e.g. `192.168.1.42`) — Android cannot use `127.0.0.1` for the host.

### 2. Android Studio

1. Open `sovereign-ecosystem/zeegate/`.
2. Copy `local.properties.example` → `local.properties`; set `sdk.dir`.
3. Sync Gradle; run on **emulator** or **physical device** (arm64).

**Emulator defaults** (`app/build.gradle.kts`):

- Mint worker: `http://10.0.2.2:8090` (host loopback from AVD)
- Node id: `zerocell-node-001`

**Physical device** — configure before or in `MainActivity`:

```kotlin
TelemetryService.configure(
    nodeId = "zerocell-node-001",
    mintWorkerUrl = "http://192.168.1.42:8090",  // host LAN IP
)
startService(Intent(this, TelemetryService::class.java))
```

### 3. SIP registration (optional, ties to Phase 3 voice)

Register gsm2sip/PJSIP leg to Kamailio:

| Field | Value |
|-------|--------|
| Domain | `zeegate.lab` |
| User | `edge001` |
| Password | `edge001` |
| Server | host LAN IP, port **5060** |

Bindings map `sip_user: edge001` → `did:tegal:LABEDGE001` ([tegalid_bindings.example.json](../../tegalchain/data/tegalid_bindings.example.json)).

### 4. Trigger telemetry

- App starts `TelemetryService` on launch.
- Reports every **30 s** (first after 5 s).
- Watch Logcat: `ZeeGate-Telemetry`, `ZeeGate-MintWorker`.

### 5. Verify on host

```bash
curl -s http://127.0.0.1:8090/v1/queue/stats | python3 -m json.tool
bash scripts/replit-mint-drain.sh 10
curl -s "http://127.0.0.1:8090/v1/telemetry/records/{gtr_id}" | python3 -m json.tool
```

Android posts to **`POST /v1/telemetry`** (legacy envelope), not `/v1/telemetry/records` — both are supported.

---

## Run — Track C (MQTT, optional)

```bash
export MINT_WORKER_MQTT_ENABLED=1
export MINT_WORKER_MQTT_BROKER=127.0.0.1
python3 -m integrations.mint_worker
```

Publish signed GTR to `gtp/{source_id}/readings`. See [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md#mqtt-v5-ingest-optional).

---

## Tegalid mode (production-shaped lab)

After Track A/B succeed in **dev** mode, replay with binding-bound DIDs:

```bash
export TEGALCHAIN_IDENTITY_MODE=tegalid
export TEGALID_BINDINGS_FILE=tegalchain/data/tegalid_bindings.json
cp tegalchain/data/tegalid_bindings.example.json tegalchain/data/tegalid_bindings.json
```

| Producer | `node_id` / `source_id` | Signing secret |
|----------|-------------------------|----------------|
| Zeegate edge | `did:tegal:LABEDGE001` | `telemetry_hmac_secret_hex` from binding |
| Bytenergy | `did:tegal:LABENERGY01` | binding `…secret02` |

Producers must sign with the binding `telemetry_hmac_secret_hex` for their DID. CDR adapter already resolves this in dev for `edge001` (≥ `5f6c9f5`).

---

## Exit criteria

- [ ] `./scripts/phase4-edge-telemetry.sh zeegate` → `gtr_id` + queue row
- [ ] `./scripts/phase4-edge-telemetry.sh bytenergy` → queue row
- [ ] Mock drain → `submitted ≥ 1` new edge-originated `gtr_id` with `LABMOCK-…`
- [ ] `GET /v1/telemetry/records/{gtr_id}` → correct `system_type` / metrics (not CDR adapter metadata)
- [ ] (Optional) Android Logcat shows mint worker `200`/`201`
- [ ] (Optional) Android registers `edge001@zeegate.lab` to Kamailio
- [ ] (Optional) MQTT ingest → ack on `gtp/{source_id}/ack`

## Phase 3 closure reference

Phase 3 live CDR (Replit lab, 2026-07-28) — example `gtr_id`s:

- `e9e4bc8f-c775-454d-b389-073df66887ad` (live echo CDR)
- Phase 2 fixture: `8717180f-9e32-4d5a-9099-8ccf08ee75ea`

Phase 4 records must use **edge producer** metadata, not `evidence_kind: CDR`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Connection refused` on POST | Start `./scripts/start-mint-worker.sh` |
| `401` attestation failed | Dev mode + default HMAC key; or tegalid secret mismatch |
| Android `HTTP 4xx` from emulator | Use `10.0.2.2:8090`, not `127.0.0.1` |
| Physical device cannot POST | Mint worker URL = host **LAN IP**; allow firewall :8090 |
| Queue `submitted` but no new row | Check `telemetry_hash` dedupe — vary timestamp/metrics |
| `curl …/records` empty JSON | Use `GET /v1/telemetry/records/{gtr_id}` with id from POST response |

## Related

- [PHASE-3.md](./PHASE-3.md) — live CDR (complete)
- [PHASE-5.md](./PHASE-5.md) — Cosmos devnet anchor
- [LAB-MINT-DRAIN.md](../runbooks/LAB-MINT-DRAIN.md)
- [TEGALID-GREETELEMETRY.md](../contracts/TEGALID-GREETELEMETRY.md)
- [zeegate/README.md](../../zeegate/README.md)
- [scripts/phase4-edge-telemetry.sh](../../scripts/phase4-edge-telemetry.sh)

## Next

[Phase 5 — Cosmos devnet anchor](./PHASE-5.md): replace `LABMOCK-…` with real `txhash` from Tegalchain devnet.
