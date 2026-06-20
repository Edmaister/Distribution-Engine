from __future__ import annotations

import json
import logging
from typing import Any, Dict

import boto3

from apps.api.settings import get_settings

logger = logging.getLogger(__name__)


def publish_to_dlq(event: Dict[str, Any], error: str) -> None:
    settings = get_settings()
    dlq_url = settings.app_sqs_dlq_url

    payload = {
        "originalEvent": event,
        "error": error,
    }

    # Local fallback (no SQS configured)
    if not dlq_url:
        logger.error(
            "DLQ_STUB_EVENT",
            extra={
                "payload": payload,
            },
        )
        return

    try:
        sqs = boto3.client("sqs", region_name="eu-west-1")

        sqs.send_message(
            QueueUrl=dlq_url,
            MessageBody=json.dumps(payload, default=str),
        )

        logger.info("DLQ_EVENT_PUBLISHED")

    except Exception:
        logger.exception("Failed to publish event to DLQ")