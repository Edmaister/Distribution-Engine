#apps/Workers/referral)events_consumer.py
# Deprecated: replaced by SQS worker
# Do not run in current deployment
from __future__ import annotations

import asyncio
import inspect
import json
import logging

from services.journey_orchestrator import handle_referral_progress_recorded
from utils.kafka import get_kafka_consumer

logger = logging.getLogger(__name__)


def run_referral_events_consumer() -> None:
    consumer = get_kafka_consumer(
        topic="referral-events",
        group_id="journey-orchestrator"
    )

    for message in consumer:
        try:
            raw = message.value
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")

            event = json.loads(raw)
            event_type = event.get("eventType")

            if event_type == "REFERRAL_PROGRESS_RECORDED":
                result = handle_referral_progress_recorded(event)
                if inspect.isawaitable(result):
                    asyncio.run(result)

        except Exception:
            logger.exception("Failed to process referral event")
