from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

import boto3

from apps.api.settings import get_settings
from services.leaderboard_service import rebuild_leaderboard_for_referrer

logger = logging.getLogger(__name__)

EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED = "LEADERBOARD_REBUILD_REQUESTED"


def _build_leaderboard_rebuild_event(
    *,
    tenant_code: str,
    referrer_ucn: str,
    correlation_id: str | None = None,
    referral_track_id: str | None = None,
) -> dict[str, Any]:
    return {
        "eventType": EVENT_TYPE_LEADERBOARD_REBUILD_REQUESTED,
        "tenantCode": tenant_code,
        "referrerUcn": referrer_ucn,
        "correlationId": correlation_id or str(uuid.uuid4()),
        "referralTrackId": referral_track_id,
    }


async def _send_sqs_message_async(
    *,
    queue_url: str,
    event: dict[str, Any],
    aws_region: str | None,
) -> dict[str, Any]:
    def _send() -> dict[str, Any]:
        sqs = boto3.client("sqs", region_name=aws_region)
        return sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(event),
        )

    return await asyncio.to_thread(_send)


async def publish_leaderboard_rebuild_requested(
    *,
    tenant_code: str,
    referrer_ucn: str,
    correlation_id: str | None = None,
    referral_track_id: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()

    event = _build_leaderboard_rebuild_event(
        tenant_code=tenant_code,
        referrer_ucn=referrer_ucn,
        correlation_id=correlation_id,
        referral_track_id=referral_track_id,
    )

    queue_url = getattr(settings, "app_sqs_queue_url", None)

    if not queue_url:
        logger.info(
            "LEADERBOARD_REBUILD_SQS_STUB",
            extra={
                "tenant_code": tenant_code,
                "referrer_ucn": referrer_ucn,
                "correlation_id": event["correlationId"],
                "referral_track_id": referral_track_id,
            },
        )

        await rebuild_leaderboard_for_referrer(
            tenant_code=tenant_code,
            referrer_ucn=referrer_ucn,
        )

        return {
            "status": "stubbed",
            "event": event,
        }

    response = await _send_sqs_message_async(
        queue_url=queue_url,
        event=event,
        aws_region=getattr(settings, "aws_region", None),
    )

    logger.info(
        "LEADERBOARD_REBUILD_EVENT_PUBLISHED",
        extra={
            "tenant_code": tenant_code,
            "referrer_ucn": referrer_ucn,
            "correlation_id": event["correlationId"],
            "referral_track_id": referral_track_id,
            "message_id": response.get("MessageId"),
        },
    )

    return {
        "status": "published",
        "event": event,
        "message_id": response.get("MessageId"),
    }