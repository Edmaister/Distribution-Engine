from __future__ import annotations

import json
from typing import Any

from services.fulfilment_status import FulfilmentStatus
from utils.db import async_db_cursor


async def create_fulfilment_audit_record(
    *,
    tenant_code: str,
    referral_track_id: str | None,
    referrer_ucn: str | None,
    referee_ucn: str | None,
    reward_type: str,
    fulfilment_provider: str,
    idempotency_key: str,
    correlation_id: str | None = None,
    event_type: str | None = None,
    max_attempts: int = 3,
) -> dict[str, Any]:
    query = """
    INSERT INTO fulfilment_audit (
        tenant_code,
        referral_track_id,
        referrer_ucn,
        referee_ucn,
        reward_type,
        fulfilment_provider,
        idempotency_key,
        status,
        correlation_id,
        event_type,
        max_attempts
    )
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
    RETURNING audit_id, status;
    """

    async with async_db_cursor() as cur:
        row = await cur.fetchrow(
            query,
            tenant_code,
            referral_track_id,
            referrer_ucn,
            referee_ucn,
            reward_type,
            fulfilment_provider,
            idempotency_key,
            FulfilmentStatus.PENDING.value,
            correlation_id,
            event_type,
            max_attempts,
        )

    return {
        "audit_id": str(row["audit_id"]),
        "status": row["status"],
    }


async def get_existing_audit_by_idempotency_key(
    idempotency_key: str,
) -> dict[str, Any] | None:
    query = """
    SELECT
        audit_id,
        status,
        provider_reference
    FROM fulfilment_audit
    WHERE idempotency_key = $1;
    """

    async with async_db_cursor() as cur:
        row = await cur.fetchrow(query, idempotency_key)

    if not row:
        return None

    return {
        "audit_id": str(row["audit_id"]),
        "status": row["status"],
        "provider_reference": row["provider_reference"],
    }


async def mark_fulfilment_processing(
    *,
    audit_id: str,
) -> None:
    query = """
    UPDATE fulfilment_audit
    SET
        previous_status = status,
        status = $1,
        processing_started_at = now(),
        updated_at = now()
    WHERE audit_id = $2;
    """

    async with async_db_cursor() as cur:
        await cur.execute(
            query,
            FulfilmentStatus.PROCESSING.value,
            audit_id,
        )


async def mark_fulfilment_success(
    *,
    audit_id: str,
    provider_reference: str | None = None,
    provider_status: str | None = None,
    provider_response: dict[str, Any] | None = None,
) -> None:
    query = """
    UPDATE fulfilment_audit
    SET
        previous_status = status,
        status = $1,
        provider_reference = $2,
        provider_status = $3,
        provider_response = $4::jsonb,
        completed_at = now(),
        updated_at = now()
    WHERE audit_id = $5;
    """

    async with async_db_cursor() as cur:
        await cur.execute(
            query,
            FulfilmentStatus.SUCCESS.value,
            provider_reference,
            provider_status,
            json.dumps(provider_response or {}),
            audit_id,
        )


async def mark_fulfilment_failed(
    *,
    audit_id: str,
    failure_reason: str,
    error_code: str | None = None,
    retryable: bool = True,
) -> None:
    status = (
        FulfilmentStatus.FAILED_RETRYABLE
        if retryable
        else FulfilmentStatus.FAILED_FINAL
    )

    query = """
    UPDATE fulfilment_audit
    SET
        previous_status = status,
        status = $1,
        failure_reason = $2,
        error_code = $3,
        failed_at = now(),
        updated_at = now()
    WHERE audit_id = $4;
    """

    async with async_db_cursor() as cur:
        await cur.execute(
            query,
            status.value,
            failure_reason,
            error_code,
            audit_id,
        )


async def increment_fulfilment_attempt(
    *,
    audit_id: str,
) -> dict[str, Any]:
    query = """
    UPDATE fulfilment_audit
    SET
        attempt_no = attempt_no + 1,
        updated_at = now()
    WHERE audit_id = $1
    RETURNING attempt_no, max_attempts;
    """

    async with async_db_cursor() as cur:
        row = await cur.fetchrow(query, audit_id)

    return {
        "attempt_no": row["attempt_no"],
        "max_attempts": row["max_attempts"],
        "retries_exhausted": row["attempt_no"] >= row["max_attempts"],
    }