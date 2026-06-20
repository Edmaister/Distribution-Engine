from __future__ import annotations

from typing import Any

from services.fulfilment_events import publish_reward_fulfilment_requested
from utils.db import async_db_cursor


REPLAYABLE_STATUSES = {
    "FAILED_RETRYABLE",
    "FAILED_FINAL",
    "DLQ",
}


async def get_fulfilment_audit_by_id(
    *,
    audit_id: str,
) -> dict[str, Any] | None:
    query = """
    SELECT
        audit_id,
        tenant_code,
        referral_track_id,
        referrer_ucn,
        referee_ucn,
        reward_type,
        fulfilment_provider,
        idempotency_key,
        status,
        attempt_no,
        max_attempts,
        correlation_id,
        event_type,
        failure_reason,
        error_code,
        provider_reference,
        provider_status,
        provider_response
    FROM fulfilment_audit
    WHERE audit_id = $1;
    """

    async with async_db_cursor() as cur:
        row = await cur.fetchrow(query, audit_id)

    return dict(row) if row else None


async def mark_fulfilment_replay_requested(
    *,
    audit_id: str,
) -> None:
    query = """
    UPDATE fulfilment_audit
    SET
        previous_status = status,
        status = 'PENDING',
        updated_at = now()
    WHERE audit_id = $1;
    """

    async with async_db_cursor() as cur:
        await cur.execute(query, audit_id)


async def replay_failed_fulfilment(
    *,
    audit_id: str,
) -> dict[str, Any]:
    audit = await get_fulfilment_audit_by_id(
        audit_id=audit_id,
    )

    if not audit:
        return {
            "status": "not_found",
            "audit_id": audit_id,
        }

    current_status = audit["status"]

    if current_status == "SUCCESS":
        return {
            "status": "skipped",
            "reason": "already_successful",
            "audit_id": audit_id,
        }

    if current_status == "PROCESSING":
        return {
            "status": "skipped",
            "reason": "currently_processing",
            "audit_id": audit_id,
        }

    if current_status not in REPLAYABLE_STATUSES:
        return {
            "status": "skipped",
            "reason": f"status_not_replayable:{current_status}",
            "audit_id": audit_id,
        }

    await mark_fulfilment_replay_requested(
        audit_id=audit_id,
    )

    event = await publish_reward_fulfilment_requested(
        tenant_code=audit["tenant_code"],
        reward_id=audit["correlation_id"] or str(audit["audit_id"]),
        reward_type=audit["reward_type"],
        reward_value=0.0,
        recipient_ucn=audit["referee_ucn"],
        currency="ZAR",
        journey_code=None,
        milestone_code=None,
        product_code=None,
        correlation_id=str(audit["correlation_id"] or audit["audit_id"]),
        metadata={
            "replay": True,
            "source_audit_id": str(audit["audit_id"]),
            "original_idempotency_key": audit["idempotency_key"],
            "referral_track_id": audit["referral_track_id"],
            "attempt_no": audit["attempt_no"],
            "max_attempts": audit["max_attempts"],
            "previous_failure_reason": audit["failure_reason"],
            "previous_error_code": audit["error_code"],
        },
    )

    return {
        "status": "replay_requested",
        "audit_id": audit_id,
        "event": event,
    }