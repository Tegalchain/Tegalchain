# ZeeGate — Android Studio project

Native **DePIN edge node** for the sovereign ecosystem: **gsm2sip gateway**, **AnyFi software-defined WiFi access gateway**, and telemetry aligned to `greentelemetry-protocol-spec/schema.json`.

Architecture (SaaS control plane → tegalid → Tegalchain → GreenLedger): [docs/platforms/ZEEGATE-DEPIN-CONTROL-PLANE.md](../docs/platforms/ZEEGATE-DEPIN-CONTROL-PLANE.md).

## DePIN client stack (three legs)

| Leg | Role |
|-----|------|
| **gsm2sip** | Stripped-down GSM↔SIP gateway (PJSIP + telephony + Oboe audio); registers to cloud Kamailio |
| **AnyFi** | Software-defined WiFi — turns the phone into a mesh/backhaul internet access gateway |
| **GreTelemetry** | Signed sovereign telemetry (`TelemetryService`, `MintWorkerClient`) — tegalid-bound identity at the oracle |

Cloud voice path (separate from AnyFi data plane): **tegalid-gated SIP credentials** → **Kamailio** (SBC) → **FreeSWITCH** (media) → Zeegate gsm2sip leg. No separate cloud orchestration agent on the device.

AnyFi provides **connectivity/backhaul** for the node and contributes to `telecom_bandwidth_bytes` metering (shared WiFi throughput, peer count).

## Open in Android Studio

1. **File → Open**
2. Select this folder:
   - **From Windows:** `\\wsl$\Ubuntu\home\shootle\sovereign-ecosystem\zeegate`
   - **Or clone the monorepo** to `AndroidStudioProjects` and open `sovereign-ecosystem/zeegate`

3. Copy SDK config if needed:
   ```bash
   cp local.properties.example local.properties
   ```
   Edit `sdk.dir` for your machine (`local.properties` is gitignored).

4. Sync Gradle and run on device/emulator.

## Open in Cursor

Open the monorepo root (`sovereign-ecosystem/`) for protocol work, Python integrations, and cross-subsystem edits. Use Android Studio for Gradle builds and the Android emulator.

## Python telemetry stub

Development/testing client (not part of this Gradle project):

```bash
python integrations/zeegate_telemetry/client.py
```

## Sync with GitHub

Same workflow as the rest of the monorepo — commit from Cursor or Android Studio, push to [Shootle/sovereign-ecosystem](https://github.com/Shootle/sovereign-ecosystem).
