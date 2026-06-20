from __future__ import annotations

from typing import Any
from uuid import uuid4

from utils.queue import enqueue_event


REWARD_FULFILMENT_REQUESTED = (
    "REWARD_FULFILMENT_REQUESTED"
)


async def publish_reward_fulfilment_requested(
    *,
    tenant_code: str,
    reward_id: str,
    reward_type: str,
    reward_value: float,
    recipient_ucn: str | None = None,
    currency: str | None = None,
    journey_code: str | None = None,
    milestone_code: str | None = None,
    product_code: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):

    event = {
        "eventType":
            REWARD_FULFILMENT_REQUESTED,

        "eventId":
            str(uuid4()),

        "correlationId":
            correlation_id or str(uuid4()),

        "tenantCode":
            tenant_code,

        "rewardId":
            reward_id,

        "rewardType":
            reward_type,

        "rewardValue":
            reward_value,

        "recipientUcn":
            recipient_ucn,

        "currency":
            currency,

        "journeyCode":
            journey_code,

        "milestoneCode":
            milestone_code,

        "productCode":
            product_code,

        "metadata":
            metadata or {},
    }

    await enqueue_event(event)

    return event