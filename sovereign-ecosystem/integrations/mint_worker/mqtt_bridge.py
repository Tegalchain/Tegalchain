"""TP-101 MQTT v5 ingestion bridge — subscribe readings, publish ack/errors."""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.gtr import ReportingMode  # noqa: E402
from greentelemetry_protocol_spec.normalize import detect_payload_kind  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter import DEFAULT_DB  # noqa: E402

from .auth import bearer_required  # noqa: E402
from .ingest import IngestError, IngestResult, ingest_payload, source_id_from_payload  # noqa: E402
from .mqtt_topics import (  # noqa: E402
    READINGS_SEGMENT,
    ack_topic,
    errors_topic,
    parse_readings_topic,
    readings_subscribe_filter,
)

logger = logging.getLogger(__name__)

PublishFn = Callable[[str, dict[str, Any]], None]


def mqtt_enabled() -> bool:
    return os.environ.get("MINT_WORKER_MQTT_ENABLED", "").lower() in {
        "1",
        "true",
        "yes",
    }


def active_transports() -> list[str]:
    transports = ["https_rest"]
    if mqtt_enabled():
        transports.append("mqtt_v5")
    return transports


@dataclass(frozen=True, slots=True)
class MqttBridgeConfig:
    broker: str
    port: int
    topic_prefix: str
    client_id: str
    username: str | None
    password: str | None
    use_tls: bool
    keepalive: int
    qos: int

    @classmethod
    def from_env(cls) -> MqttBridgeConfig:
        password = os.environ.get("MINT_WORKER_MQTT_PASSWORD", "").strip() or None
        if password is None and bearer_required():
            password = os.environ.get("MINT_WORKER_BEARER_TOKEN", "").strip() or None
        username = os.environ.get("MINT_WORKER_MQTT_USERNAME", "").strip() or None
        if username is None and password is not None:
            username = "gtp"
        return cls(
            broker=os.environ.get("MINT_WORKER_MQTT_BROKER", "localhost"),
            port=int(os.environ.get("MINT_WORKER_MQTT_PORT", "1883")),
            topic_prefix=os.environ.get("MINT_WORKER_MQTT_TOPIC_PREFIX", "gtp"),
            client_id=os.environ.get(
                "MINT_WORKER_MQTT_CLIENT_ID",
                f"mint-worker-mqtt-{uuid.uuid4().hex[:8]}",
            ),
            username=username,
            password=password,
            use_tls=os.environ.get("MINT_WORKER_MQTT_TLS", "").lower()
            in {"1", "true", "yes"},
            keepalive=int(os.environ.get("MINT_WORKER_MQTT_KEEPALIVE", "60")),
            qos=int(os.environ.get("MINT_WORKER_MQTT_QOS", "1")),
        )


def build_ack_message(result: IngestResult) -> dict[str, Any]:
    return {
        "gtr_id": result.gtr_id,
        "queue_id": result.queue_id,
        "status": result.status,
        "ledger_ref": result.ledger_ref,
    }


def build_error_message(
    *,
    source_id: str | None,
    error: str,
    status_code: int,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": error,
        "status_code": status_code,
    }
    if source_id is not None:
        body["source_id"] = source_id
    return body


def process_mqtt_ingest(
    store: MintQueueStore,
    topic: str,
    payload_bytes: bytes,
    *,
    topic_prefix: str = "gtp",
    reporting_mode: ReportingMode = ReportingMode.STREAM,
) -> tuple[str, dict[str, Any], str | None]:
    """Parse topic + JSON payload, run ingest pipeline.

    Returns ``(outcome, message, source_id)`` where outcome is ``ack`` or ``error``.
    """
    topic_source = parse_readings_topic(topic, prefix=topic_prefix)
    if topic_source is None:
        return (
            "error",
            build_error_message(
                source_id=None,
                error=f"unsupported topic (expected {topic_prefix}/{{source_id}}/{READINGS_SEGMENT})",
                status_code=400,
            ),
            None,
        )

    try:
        payload_text = payload_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return (
            "error",
            build_error_message(
                source_id=topic_source,
                error="payload must be UTF-8 JSON",
                status_code=400,
            ),
            topic_source,
        )

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        return (
            "error",
            build_error_message(
                source_id=topic_source,
                error=f"invalid JSON: {exc.msg}",
                status_code=400,
            ),
            topic_source,
        )

    if not isinstance(payload, dict):
        return (
            "error",
            build_error_message(
                source_id=topic_source,
                error="payload must be a JSON object",
                status_code=400,
            ),
            topic_source,
        )

    try:
        kind = detect_payload_kind(payload)
        payload_source = source_id_from_payload(payload, kind)
    except (KeyError, TypeError, ValueError) as exc:
        return (
            "error",
            build_error_message(
                source_id=topic_source,
                error=str(exc),
                status_code=400,
            ),
            topic_source,
        )

    if payload_source != topic_source:
        return (
            "error",
            build_error_message(
                source_id=topic_source,
                error=(
                    f"topic source_id {topic_source!r} does not match "
                    f"payload source {payload_source!r}"
                ),
                status_code=400,
            ),
            topic_source,
        )

    try:
        result = ingest_payload(
            store,
            payload,
            reporting_mode=reporting_mode,
        )
    except IngestError as exc:
        return (
            "error",
            build_error_message(
                source_id=topic_source,
                error=str(exc),
                status_code=exc.status_code,
            ),
            topic_source,
        )

    return ("ack", build_ack_message(result), topic_source)


def handle_mqtt_message(
    store: MintQueueStore,
    topic: str,
    payload_bytes: bytes,
    publish: PublishFn,
    *,
    topic_prefix: str = "gtp",
    reporting_mode: ReportingMode = ReportingMode.STREAM,
) -> None:
    outcome, message, source_id = process_mqtt_ingest(
        store,
        topic,
        payload_bytes,
        topic_prefix=topic_prefix,
        reporting_mode=reporting_mode,
    )
    if source_id is None:
        logger.warning("mqtt ingest rejected topic=%s error=%s", topic, message.get("error"))
        return
    if outcome == "ack":
        publish(ack_topic(source_id), message)
    else:
        publish(errors_topic(source_id), message)


def default_queue_store() -> MintQueueStore:
    db_path = Path(os.environ.get("TEGALCHAIN_MINT_QUEUE_DB", str(DEFAULT_DB)))
    return MintQueueStore(db_path)


class MqttBridge:
    """Background MQTT v5 subscriber wired to the mint queue ingest pipeline."""

    def __init__(
        self,
        store: MintQueueStore,
        config: MqttBridgeConfig | None = None,
    ) -> None:
        self._store = store
        self._config = config or MqttBridgeConfig.from_env()
        self._client: Any | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def config(self) -> MqttBridgeConfig:
        return self._config

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="mint-worker-mqtt", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._client is not None:
            try:
                self._client.disconnect()
            except Exception:  # noqa: BLE001 — best-effort shutdown
                logger.exception("mqtt disconnect failed")
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            self._thread = None

    def _publish_json(self, topic: str, payload: dict[str, Any]) -> None:
        if self._client is None:
            return
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        self._client.publish(topic, encoded, qos=self._config.qos)

    def _on_message(self, _client: Any, _userdata: Any, message: Any) -> None:
        try:
            handle_mqtt_message(
                self._store,
                message.topic,
                message.payload,
                self._publish_json,
                topic_prefix=self._config.topic_prefix,
            )
        except Exception:  # noqa: BLE001 — isolate handler failures per message
            logger.exception("mqtt message handler failed topic=%s", message.topic)

    def _run(self) -> None:
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError(
                "paho-mqtt is required for MQTT bridge (pip install paho-mqtt)"
            ) from exc

        client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=self._config.client_id,
            protocol=mqtt.MQTTv5,
        )
        self._client = client

        if self._config.username is not None:
            client.username_pw_set(self._config.username, self._config.password)

        if self._config.use_tls:
            client.tls_set()

        client.on_message = self._on_message

        subscribe_filter = readings_subscribe_filter(prefix=self._config.topic_prefix)
        logger.info(
            "mqtt bridge connecting broker=%s:%s subscribe=%s",
            self._config.broker,
            self._config.port,
            subscribe_filter,
        )
        client.connect(
            self._config.broker,
            self._config.port,
            keepalive=self._config.keepalive,
        )
        client.subscribe(subscribe_filter, qos=self._config.qos)
        while not self._stop_event.is_set():
            client.loop(timeout=1.0)


def maybe_start_mqtt_bridge(store: MintQueueStore | None = None) -> MqttBridge | None:
    if not mqtt_enabled():
        return None
    bridge = MqttBridge(store or default_queue_store())
    bridge.start()
    return bridge


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not mqtt_enabled():
        os.environ["MINT_WORKER_MQTT_ENABLED"] = "1"
    bridge = MqttBridge(default_queue_store())
    bridge.start()
    logger.info("mqtt bridge running (Ctrl+C to stop)")
    try:
        while True:
            bridge._stop_event.wait(timeout=3600)
            if bridge._stop_event.is_set():
                break
    except KeyboardInterrupt:
        logger.info("mqtt bridge stopping")
    finally:
        bridge.stop()


if __name__ == "__main__":
    main()
