from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import time
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from services.journey_orchestrator import handle_referral_progress_recorded
from apps.core.logging_utils import log_event
from services.failure_governance_service import (
    classify_processing_failure,
    record_event_failure,
)

logger = logging.getLogger(__name__)

SQS_QUEUE_URL = os.environ.get("APP_SQS_QUEUE_URL", "")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")

# Tunables
WAIT_TIME_SECONDS = int(os.environ.get("APP_SQS_WAIT_TIME_SECONDS", "10"))
MAX_NUMBER_OF_MESSAGES = int(os.environ.get("APP_SQS_MAX_MESSAGES", "5"))
VISIBILITY_TIMEOUT = int(os.environ.get("APP_SQS_VISIBILITY_TIMEOUT", "60"))
IDLE_SLEEP_SECONDS = float(os.environ.get("APP_SQS_IDLE_SLEEP_SECONDS", "2"))


def _get_sqs_client():
    return boto3.client("sqs", region_name=AWS_REGION)


def _parse_message_body(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse SQS message body into a dict.
    Supports:
    - direct JSON body
    - SNS-wrapped body delivered into SQS
    """
    raw_body = msg.get("Body", "")
    body = json.loads(raw_body)

    # Handle SNS -> SQS fanout wrapper if ever introduced later
    if isinstance(body, dict) and "Message" in body:
        nested = body["Message"]
        if isinstance(nested, str):
            return json.loads(nested)
        if isinstance(nested, dict):
            return nested

    if not isinstance(body, dict):
        raise ValueError("SQS message body is not a JSON object")

    return body


def _log_worker_received(event: Dict[str, Any], message_id: str | None) -> None:
    referral_track_id = event.get("referralTrackId") or event.get("referral_track_id")
    correlation_id = event.get("correlationId") or event.get("correlation_id") or referral_track_id
    source_event_id = event.get("sourceEventId") or event.get("source_event_id") or message_id
    source_system = event.get("sourceSystem") or event.get("source_system") or "sqs"
    event_type = event.get("eventType")

    log_event(
        level="INFO",
        component="worker",
        message="worker_received_payload",
        correlation_id=correlation_id,
        referral_track_id=referral_track_id,
        source_event_id=source_event_id,
        source_system=source_system,
        event_type=event_type,
        extra={
            "message_id": message_id,
            "raw_payload_keys": sorted(list(event.keys())),
        },
    )


def _log_payload_unwrapped(event: Dict[str, Any], message_id: str | None) -> None:
    referral_track_id = event.get("referralTrackId") or event.get("referral_track_id")
    correlation_id = event.get("correlationId") or event.get("correlation_id") or referral_track_id
    source_event_id = event.get("sourceEventId") or event.get("source_event_id") or message_id
    source_system = event.get("sourceSystem") or event.get("source_system") or "sqs"

    progress_event_type = (
        event.get("progressEventType")
        or event.get("progress_event_type")
        or event.get("eventType")
    )

    log_event(
        level="INFO",
        component="worker",
        message="payload_unwrapped",
        correlation_id=correlation_id,
        referral_track_id=referral_track_id,
        source_event_id=source_event_id,
        source_system=source_system,
        event_type=event.get("eventType"),
        extra={
            "message_id": message_id,
            "progress_event_type": progress_event_type,
        },
    )


def _process_event(event: Dict[str, Any], message_id: str | None) -> None:
    event_type = event.get("eventType")
    referral_track_id = event.get("referralTrackId") or event.get("referral_track_id")
    correlation_id = event.get("correlationId") or event.get("correlation_id") or referral_track_id
    source_event_id = event.get("sourceEventId") or event.get("source_event_id") or message_id
    source_system = event.get("sourceSystem") or event.get("source_system") or "sqs"

    _log_worker_received(event, message_id)
    _log_payload_unwrapped(event, message_id)

    if event_type == "REFERRAL_PROGRESS_RECORDED":
        log_event(
            level="INFO",
            component="worker",
            message="worker_routing_event",
            correlation_id=correlation_id,
            referral_track_id=referral_track_id,
            source_event_id=source_event_id,
            source_system=source_system,
            event_type=event_type,
            extra={
                "message_id": message_id,
                "progress_event_type": event.get("progressEventType"),
                "route": "handle_referral_progress_recorded",
            },
        )

        result = handle_referral_progress_recorded(event)
        if inspect.isawaitable(result):
            asyncio.run(result)
        return

    log_event(
        level="WARNING",
        component="worker",
        message="worker_ignored_unsupported_event",
        correlation_id=correlation_id,
        referral_track_id=referral_track_id,
        source_event_id=source_event_id,
        source_system=source_system,
        event_type=event_type,
        extra={
            "message_id": message_id,
        },
    )


def run_sqs_referral_worker() -> None:
    if not SQS_QUEUE_URL:
        raise RuntimeError("APP_SQS_QUEUE_URL is not configured")

    sqs = _get_sqs_client()

    logger.info(
        "Starting SQS referral worker | queue=%s | region=%s",
        SQS_QUEUE_URL,
        AWS_REGION,
    )

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=min(MAX_NUMBER_OF_MESSAGES, 10),
                WaitTimeSeconds=WAIT_TIME_SECONDS,
                VisibilityTimeout=VISIBILITY_TIMEOUT,
                MessageAttributeNames=["All"],
                AttributeNames=["All"],
            )

            messages = response.get("Messages", [])

            if not messages:
                time.sleep(IDLE_SLEEP_SECONDS)
                continue

            for msg in messages:
                message_id = msg.get("MessageId")
                receipt_handle = msg.get("ReceiptHandle")

                try:
                    event = _parse_message_body(msg)

                    _process_event(event, message_id)

                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=receipt_handle,
                    )

                    referral_track_id = event.get("referralTrackId") or event.get("referral_track_id")
                    correlation_id = event.get("correlationId") or event.get("correlation_id") or referral_track_id
                    source_event_id = event.get("sourceEventId") or event.get("source_event_id") or message_id
                    source_system = event.get("sourceSystem") or event.get("source_system") or "sqs"

                    log_event(
                        level="INFO",
                        component="worker",
                        message="worker_message_deleted",
                        correlation_id=correlation_id,
                        referral_track_id=referral_track_id,
                        source_event_id=source_event_id,
                        source_system=source_system,
                        event_type=event.get("eventType"),
                        extra={"message_id": message_id},
                    )

                except Exception as exc:
                    event = None
                    referral_track_id = None
                    correlation_id = message_id
                    source_event_id = message_id
                    source_system = "sqs"
                    event_type = None

                    try:
                        event = _parse_message_body(msg)
                        referral_track_id = event.get("referralTrackId") or event.get("referral_track_id")
                        correlation_id = event.get("correlationId") or event.get("correlation_id") or referral_track_id or message_id
                        source_event_id = event.get("sourceEventId") or event.get("source_event_id") or message_id
                        source_system = event.get("sourceSystem") or event.get("source_system") or "sqs"
                        event_type = event.get("eventType")
                    except Exception:
                        pass

                    failure_category = classify_processing_failure(exc)

                    try:
                        record_event_failure(
                            event=event,
                            message_id=message_id,
                            failure_category=failure_category,
                            failure_reason=str(exc),
                        )
                    except Exception:
                        logger.exception("Failed to persist failure record")

                    log_event(
                        level="ERROR",
                        component="worker",
                        message="worker_processing_failed",
                        correlation_id=correlation_id,
                        referral_track_id=referral_track_id,
                        source_event_id=source_event_id,
                        source_system=source_system,
                        event_type=event_type,
                        extra={
                            "message_id": message_id,
                            "error": str(exc),
                            "failure_category": failure_category,
                        },
                    )

                    logger.exception("Failed processing SQS message_id=%s", message_id)

                    if failure_category in ("TRANSIENT", "SYSTEM_BUG"):
                        raise

                    # BUSINESS_RULE and DATA_QUALITY:
                    # do not raise, so we avoid poison-message retry loops

        except (BotoCoreError, ClientError) as exc:
            log_event(
                level="ERROR",
                component="worker",
                message="worker_receive_loop_failed",
                correlation_id="sqs-receive-loop",
                source_system="sqs",
                extra={"error": str(exc)},
            )
            logger.exception("SQS receive loop failed")
            time.sleep(5)

        except Exception as exc:
            log_event(
                level="ERROR",
                component="worker",
                message="worker_unexpected_failure",
                correlation_id="worker-main-loop",
                source_system="sqs",
                extra={"error": str(exc)},
            )
            logger.exception("Unexpected worker failure")
            time.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    run_sqs_referral_worker()
