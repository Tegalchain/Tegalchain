# Telemetry Integration

Real-time and near-real-time telemetry from regenerative sources is fundamental for PoR PoRE evidence.

Data sources
- Smart meters (IEC 61850), IoT sensors (LoRaWAN, MQTT), grid SCADA, camera traps, acoustic sensors, water and soil sensors.

Pipeline (recommended)
1. Ingest: MQTT / Kafka ingestion with Python `telemetry-collector`.
2. Validate: `energy-validator` / `poree-validator` run anomaly detection and EQS scoring.
3. Commit: cryptographic commitment to PoREvidence registry (hash stored on-chain).
4. Consensus: PoREF validators verify evidence and accept/reject block proposals.
5. Tokenization: PoREX contracts mint tX* tokens based on verified RIV.

Performance
- Target telemetry latency: <500ms for energy-critical metrics; critical evidence aggregated every 1–10s for block validation.
