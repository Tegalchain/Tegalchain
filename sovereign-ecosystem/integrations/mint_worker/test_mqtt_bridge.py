"""Tests for TP-101 MQTT v5 bridge (no live broker required)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import Metrics, SovereignNodeTelemetry, SystemType  # noqa: E402
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from greentelemetry_protocol_spec.models import MeasurementType, SourceType  # noqa: E402
from integrations.mint_worker.mqtt_bridge import (  # noqa: E402
    MqttBridgeConfig,
    active_transports,
    handle_mqtt_message,
    mqtt_enabled,
    process_mqtt_ingest,
)
from integrations.mint_worker.mqtt_topics import (  # noqa: E402
    ack_topic,
    errors_topic,
    parse_readings_topic,
    readings_subscribe_filter,
    readings_topic,
)
from integrations.mint_worker.server import _queue_store, app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402


def _signed_legacy(node_id: str = "mqtt-node-001") -> dict:
    unsigned = SovereignNodeTelemetry(
        node_id=node_id,
        timestamp=int(time.time()),
        system_type=SystemType.ZEEGATE_TELECOM,
        metrics=Metrics(telecom_bandwidth_bytes=1024),
        signature="",
    )
    payload = unsigned.to_dict()
    payload["signature"] = sign_payload(unsigned_canonical_json(payload))
    return payload


def _signed_gtr(source_id: str = "mqtt-node-001") -> dict:
    record = build_signed_tp101_gtr(
        source_id=source_id,
        source_type=SourceType.SENSOR,
        measurement_type=MeasurementType.CUSTOM,
        value=1024.0,
        unit="bytes",
        metadata={"system_type": "ZEEGATE_TELECOM"},
    )
    return record.to_dict()


class MqttTopicTests(unittest.TestCase):
    def test_parse_readings_topic(self) -> None:
        self.assertEqual(parse_readings_topic("gtp/sensor-42/readings"), "sensor-42")
        self.assertIsNone(parse_readings_topic("gtp/sensor-42/ack"))
        self.assertIsNone(parse_readings_topic("other/sensor-42/readings"))

    def test_topic_helpers(self) -> None:
        self.assertEqual(readings_topic("lab-1"), "gtp/lab-1/readings")
        self.assertEqual(ack_topic("lab-1"), "gtp/lab-1/ack")
        self.assertEqual(errors_topic("lab-1"), "gtp/lab-1/errors")
        self.assertEqual(readings_subscribe_filter(), "gtp/+/readings")


class MqttIngestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "dev"
        self.store = MintQueueStore(Path(self.tmp.name) / "mint_queue.db")
        self.published: list[tuple[str, dict]] = []

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("TEGALCHAIN_IDENTITY_MODE", None)

    def _publish(self, topic: str, payload: dict) -> None:
        self.published.append((topic, payload))

    def test_process_legacy_payload_ack(self) -> None:
        node_id = "mqtt-node-001"
        payload = _signed_legacy(node_id)
        outcome, message, source_id = process_mqtt_ingest(
            self.store,
            readings_topic(node_id),
            json.dumps(payload).encode(),
        )
        self.assertEqual(outcome, "ack")
        self.assertEqual(source_id, node_id)
        self.assertEqual(message["status"], "pending")
        self.assertIsNone(message["ledger_ref"])
        self.assertGreaterEqual(message["queue_id"], 1)
        self.assertTrue(message["gtr_id"])

    def test_process_gtr_v1_payload_ack(self) -> None:
        payload = _signed_gtr()
        outcome, message, source_id = process_mqtt_ingest(
            self.store,
            readings_topic(payload["source_id"]),
            json.dumps(payload).encode(),
        )
        self.assertEqual(outcome, "ack")
        self.assertEqual(source_id, payload["source_id"])
        self.assertEqual(message["gtr_id"], payload["gtr_id"])

    def test_topic_source_mismatch_error(self) -> None:
        payload = _signed_legacy("payload-node")
        outcome, message, source_id = process_mqtt_ingest(
            self.store,
            readings_topic("topic-node"),
            json.dumps(payload).encode(),
        )
        self.assertEqual(outcome, "error")
        self.assertEqual(source_id, "topic-node")
        self.assertEqual(message["status_code"], 400)
        self.assertIn("does not match", message["error"])

    def test_invalid_json_error(self) -> None:
        outcome, message, source_id = process_mqtt_ingest(
            self.store,
            readings_topic("mqtt-node-001"),
            b"not-json",
        )
        self.assertEqual(outcome, "error")
        self.assertEqual(source_id, "mqtt-node-001")
        self.assertEqual(message["status_code"], 400)

    def test_bad_signature_error(self) -> None:
        payload = _signed_legacy()
        payload["signature"] = "hmac-sha256:" + "0" * 64
        outcome, message, _source_id = process_mqtt_ingest(
            self.store,
            readings_topic(payload["node_id"]),
            json.dumps(payload).encode(),
        )
        self.assertEqual(outcome, "error")
        self.assertEqual(message["status_code"], 401)

    def test_handle_message_routes_ack_and_error(self) -> None:
        good = _signed_legacy("route-node")
        handle_mqtt_message(
            self.store,
            readings_topic("route-node"),
            json.dumps(good).encode(),
            self._publish,
        )
        self.assertEqual(len(self.published), 1)
        topic, body = self.published[0]
        self.assertEqual(topic, ack_topic("route-node"))
        self.assertEqual(body["status"], "pending")

        bad = dict(good)
        bad["signature"] = "hmac-sha256:" + "1" * 64
        handle_mqtt_message(
            self.store,
            readings_topic("route-node"),
            json.dumps(bad).encode(),
            self._publish,
        )
        self.assertEqual(len(self.published), 2)
        err_topic, err_body = self.published[1]
        self.assertEqual(err_topic, errors_topic("route-node"))
        self.assertEqual(err_body["status_code"], 401)


class MqttConfigTests(unittest.TestCase):
    def tearDown(self) -> None:
        for key in (
            "MINT_WORKER_MQTT_ENABLED",
            "MINT_WORKER_BEARER_TOKEN",
            "MINT_WORKER_MQTT_PASSWORD",
            "MINT_WORKER_MQTT_USERNAME",
        ):
            os.environ.pop(key, None)

    def test_mqtt_enabled_flag(self) -> None:
        os.environ["MINT_WORKER_MQTT_ENABLED"] = "1"
        self.assertTrue(mqtt_enabled())
        self.assertEqual(active_transports(), ["https_rest", "mqtt_v5"])

    def test_config_uses_bearer_as_mqtt_password(self) -> None:
        os.environ["MINT_WORKER_BEARER_TOKEN"] = "lab-secret"
        os.environ["TEGALCHAIN_REQUIRE_BEARER"] = "1"
        cfg = MqttBridgeConfig.from_env()
        self.assertEqual(cfg.password, "lab-secret")
        self.assertEqual(cfg.username, "gtp")


class MqttHealthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["TEGALCHAIN_IDENTITY_MODE"] = "dev"
        os.environ.pop("TEGALCHAIN_REQUIRE_BEARER", None)
        os.environ.pop("MINT_WORKER_BEARER_TOKEN", None)
        os.environ["TEGALCHAIN_MINT_QUEUE_DB"] = str(Path(self.tmp.name) / "mint_queue.db")
        _queue_store.cache_clear()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        _queue_store.cache_clear()
        self.tmp.cleanup()
        os.environ.pop("TEGALCHAIN_MINT_QUEUE_DB", None)
        os.environ.pop("TEGALCHAIN_REQUIRE_BEARER", None)
        os.environ.pop("MINT_WORKER_BEARER_TOKEN", None)
        os.environ.pop("MINT_WORKER_MQTT_ENABLED", None)

    def test_health_lists_mqtt_when_enabled(self) -> None:
        os.environ["MINT_WORKER_MQTT_ENABLED"] = "1"
        with patch(
            "integrations.mint_worker.server.maybe_start_mqtt_bridge",
            return_value=None,
        ):
            client = TestClient(app)
            body = client.get("/health").json()
            self.assertIn("mqtt_v5", body["transports"])


if __name__ == "__main__":
    unittest.main()
