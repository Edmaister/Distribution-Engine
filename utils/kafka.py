"""Kafka publishing and consuming helpers with safe fallbacks."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

BROKER = os.environ.get("APP_KAFKA_BROKER", "localhost:9092")
CLIENT = os.environ.get("APP_KAFKA_CLIENT", "").lower() or "stdout"

_producer = None
_backend = "stdout"


def _init() -> None:
    global _producer, _backend

    if CLIENT == "confluent":
        try:
            from confluent_kafka import Producer

            _producer = Producer({"bootstrap.servers": BROKER})
            _backend = "confluent"
            return
        except Exception as e:
            logger.warning("confluent_kafka not available: %s", e)

    if CLIENT in ("kafka-python", "kafka"):
        try:
            from kafka import KafkaProducer

            _producer = KafkaProducer(
                bootstrap_servers=BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            _backend = "kafka-python"
            return
        except Exception as e:
            logger.warning("kafka-python not available: %s", e)

    _producer = None
    _backend = "stdout"


_init()


def publish_event(topic: str, payload: Dict[str, Any]) -> None:
    payload = dict(payload or {})

    if _backend == "confluent" and _producer:
        try:
            _producer.produce(topic, json.dumps(payload).encode("utf-8"))
            _producer.poll(0)
            return
        except Exception as e:
            logger.error("confluent publish failed: %s", e)

    elif _backend == "kafka-python" and _producer:
        try:
            _producer.send(topic, payload)
            return
        except Exception as e:
            logger.error("kafka-python publish failed: %s", e)

    logger.info(
        "event_fallback",
        extra={
            "event_type": topic,
            "payload": payload,
            "backend": _backend,
        },
    )


def get_kafka_consumer(topic: str, group_id: str) -> Any:
    from kafka import KafkaConsumer

    return KafkaConsumer(
        topic,
        bootstrap_servers=BROKER,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: v,
    )
