# Zeegate changelog

Product generations: **v1**, **v2**, … (major semver matches generation).

## [1.1.0] — Zeegate v1 (Phase 1b)

- Spec-compliant greentelemetry telemetry from `TelemetryService`
- HMAC signing aligned with `greentelemetry_protocol_spec/signing.py`
- POST to Phase 1 mint worker (`GreTelemetry`, `MintWorkerClient`, `BandwidthMeter`)

## [1.0.0] — Zeegate v1 (2026-07-26)

First monorepo baseline (generation 1).

- gsm2sip-derived DePIN client (PJSIP, Oboe, KernelSU/root audio patches)
- AnyFi software-defined WiFi gateway scaffold (permissions + telemetry stub)
- Telemetry service + blockchain bridge stub
- Protocol target: greentelemetry **1.0.0** (`telecom_bandwidth_bytes`)

### Not yet in v1

- Kamailio / FreeSWITCH lab registration (see `zeegate-cloud/`)
- Schema-valid signed telemetry from device in all build flavors
- Production gsm2sip call flow (`initPjsip` wired end-to-end)

## [Unreleased] — Zeegate v2 (planned)

- tegalid-gated edge identity + Kamailio registration against `zeegate-cloud` lab
- Cloud media path (Kamailio → FreeSWITCH → gsm2sip)
- AnyFi SDK integration + relay metering
- Native TP-101 GTR v1 emission from device (optional alongside legacy envelope)
