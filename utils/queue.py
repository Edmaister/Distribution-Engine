from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import aiofiles

from apps.core.logging_utils import log_event

SQS_QUEUE_URL = os.environ.get("APP_SQS_QUEUE_URL", "")
AWS_REGION = os.environ.get("AWS_REGION")
LOCAL_QUEUE_FILE = os.environ.get("LOCAL_QUEUE_FILE", "local_events.jsonl")


class _MissingAioboto3:
    def Session(self) -> None:
        raise RuntimeError("aioboto3 is required when APP_SQS_QUEUE_URL is set")


aioboto3 = _MissingAioboto3()


async def _write_to_local_queue(payload: dict[str, Any]) -> None:
    queue_path = Path(LOCAL_QUEUE_FILE)
    queue_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(queue_path, "a", encoding="utf-8") as f:
        await f.write(json.dumps(payload, default=str) + "\n")

    log_event(
        level="INFO",
        component="queue",
        message="LOCAL_EVENT_QUEUED",
        extra={
            "queue_file": str(queue_path),
            "eventType": payload.get("eventType"),
            "referralTrackId": payload.get("referralTrackId"),
            "rewardId": payload.get("rewardId"),
            "tenantCode": payload.get("tenantCode"),
        },
    )


async def enqueue_event(payload: dict[str, Any]) -> None:
    """
    Fully async event publisher.

    AWS mode:
        API -> SQS -> worker

    Local mode:
        API -> local_events.jsonl -> local_worker.py
    """

    if not SQS_QUEUE_URL:
        await _write_to_local_queue(payload)
        return

    global aioboto3
    if isinstance(aioboto3, _MissingAioboto3) and "Session" not in aioboto3.__dict__:
        try:
            import aioboto3 as aioboto3_module
        except ModuleNotFoundError as exc:
            raise RuntimeError("aioboto3 is required when APP_SQS_QUEUE_URL is set") from exc
        aioboto3 = aioboto3_module

    session = aioboto3.Session()

    async with session.client("sqs", region_name=AWS_REGION) as sqs:
        await sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(payload, default=str),
        )

    log_event(
        level="INFO",
        component="queue",
        message="SQS_MESSAGE_SENT",
        extra={
            "queue_url_present": True,
            "eventType": payload.get("eventType"),
            "referralTrackId": payload.get("referralTrackId"),
            "rewardId": payload.get("rewardId"),
            "sourceSystem": payload.get("sourceSystem"),
            "sourceEventId": payload.get("sourceEventId"),
            "tenantCode": payload.get("tenantCode"),
        },
    )
