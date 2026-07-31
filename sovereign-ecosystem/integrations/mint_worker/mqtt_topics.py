"""TP-101 MQTT v5 topic patterns (ingestion transport).

Messages on these topics MUST be JSON conforming to the GTR schema (Section 2.1).
Implementations MUST support HTTPS REST and MAY attach an MQTT v5 bridge using these topics.
"""

from __future__ import annotations

TOPIC_PREFIX = "gtp"
READINGS_SEGMENT = "readings"
ACK_SEGMENT = "ack"
ERRORS_SEGMENT = "errors"

TOPIC_READINGS = "gtp/{source_id}/readings"
TOPIC_ACK = "gtp/{source_id}/ack"
TOPIC_ERRORS = "gtp/{source_id}/errors"
TOPIC_READINGS_SUBSCRIBE = "gtp/+/readings"


def readings_topic(source_id: str) -> str:
    """Sensor → gateway: publish raw GTR readings."""
    return TOPIC_READINGS.format(source_id=source_id)


def ack_topic(source_id: str) -> str:
    """Gateway → sensor: subscribe for anchoring acknowledgement."""
    return TOPIC_ACK.format(source_id=source_id)


def errors_topic(source_id: str) -> str:
    """Gateway → sensor: delivery / validation error notifications."""
    return TOPIC_ERRORS.format(source_id=source_id)


def readings_subscribe_filter(*, prefix: str = TOPIC_PREFIX) -> str:
    """Wildcard filter for all source readings topics."""
    return f"{prefix}/+/{READINGS_SEGMENT}"


def parse_readings_topic(topic: str, *, prefix: str = TOPIC_PREFIX) -> str | None:
    """Return ``source_id`` from ``{prefix}/{source_id}/readings`` or ``None``."""
    parts = topic.split("/")
    if len(parts) != 3:
        return None
    if parts[0] != prefix or parts[2] != READINGS_SEGMENT:
        return None
    source_id = parts[1].strip()
    if not source_id:
        return None
    return source_id
