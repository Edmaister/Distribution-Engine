from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from services.fulfilment_events import publish_reward_fulfilment_requested
from services.fulfilment_retry_policy_service import (
    FulfilmentRetryPolicy,
    get_next_retry_delay_seconds,
)


def calculate_next_retry_at(
    *,
    policy: FulfilmentRetryPolicy,
    attempt_no: int,
    now: datetime | None = None,
) -> datetime:
    current_time = now or datetime.now(timezone.utc)

    delay_seconds = get_next_retry_delay_seconds(
        policy=policy,
        attempt_no=attempt_no,
    )

    return current_time + timedelta(seconds=delay_seconds)


def build_fulfilment_retry_metadata(
    *,
    audit_id: str,
    idempotency_key: str,
    attempt_no: int,
    max_attempts: int,
    next_retry_at: datetime,
    failure_reason: str,
    existing_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        **(existing_metadata or {}),
        "retry": True,
        "source_audit_id": audit_id,
        "idempotency_key": idempotency_key,
        "attempt_no": attempt_no,
        "max_attempts": max_attempts,
        "next_retry_at": next_retry_at.isoformat(),
        "failure_reason": failure_reason,
    }


async def schedule_fulfilment_retry(
    *,
    tenant_code: str,
    reward_id: str,
    reward_type: str,
    reward_value: float,
    recipient_ucn: str | None,
    currency: str | None,
    journey_code: str | None,
    milestone_code: str | None,
    product_code: str | None,
    audit_id: str,
    idempotency_key: str,
    attempt_no: int,
    max_attempts: int,
    policy: FulfilmentRetryPolicy,
    failure_reason: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    next_retry_at = calculate_next_retry_at(
        policy=policy,
        attempt_no=attempt_no,
    )

    retry_metadata = build_fulfilment_retry_metadata(
        audit_id=audit_id,
        idempotency_key=idempotency_key,
        attempt_no=attempt_no,
        max_attempts=max_attempts,
        next_retry_at=next_retry_at,
        failure_reason=failure_reason,
        existing_metadata=metadata,
    )

    event = await publish_reward_fulfilment_requested(
        tenant_code=tenant_code,
        reward_id=reward_id,
        reward_type=reward_type,
        reward_value=reward_value,
        recipient_ucn=recipient_ucn,
        currency=currency,
        journey_code=journey_code,
        milestone_code=milestone_code,
        product_code=product_code,
        correlation_id=reward_id,
        metadata=retry_metadata,
    )

    return {
        "status": "retry_scheduled",
        "audit_id": audit_id,
        "attempt_no": attempt_no,
        "max_attempts": max_attempts,
        "next_retry_at": next_retry_at.isoformat(),
        "event": event,
    }