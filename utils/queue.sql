from __future__ import annotations

import json
import os
from typing import Any, Dict

import boto3

SQS_QUEUE_URL = os.environ.get("APP_SQS_QUEUE_URL", "")


def enqueue_event(payload: Dict[str, Any]) -> None:
    if not SQS_QUEUE_URL:
        print(f"[SQS-STUB] {json.dumps(payload, ensure_ascii=False)}")
        return

    sqs = boto3.client("sqs", region_name=os.environ.get("AWS_REGION"))
    sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=json.dumps(payload),
    )