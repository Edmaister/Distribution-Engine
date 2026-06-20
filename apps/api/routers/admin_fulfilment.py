from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from services.fulfilment_replay_service import (
    get_fulfilment_audit_by_id,
    replay_failed_fulfilment,
)

from services.fulfilment_provider_health_service import (
    get_provider_health,
    list_provider_health,
)

from utils.db import async_db_cursor
from utils.security import require_admin_key


router = APIRouter(
    prefix="/admin/fulfilment",
    tags=["Admin Fulfilment"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("/audit/{audit_id}")
async def get_fulfilment_audit(
    audit_id: str,
):
    audit = await get_fulfilment_audit_by_id(
        audit_id=audit_id,
    )

    if not audit:
        return {
            "status": "not_found",
            "audit_id": audit_id,
        }

    return {
        "status": "ok",
        "audit": audit,
    }


@router.get("/failures")
async def list_fulfilment_failures(
    tenant_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
):
    where = """
    WHERE status IN (
        'FAILED_RETRYABLE',
        'FAILED_FINAL',
        'DLQ'
    )
    """

    params = []

    if tenant_code:
        params.append(tenant_code)
        where += f" AND tenant_code = ${len(params)}"

    params.append(limit)
    limit_placeholder = f"${len(params)}"

    query = f"""
    SELECT
        audit_id,
        tenant_code,
        referral_track_id,
        referee_ucn,
        reward_type,
        fulfilment_provider,
        idempotency_key,
        status,
        attempt_no,
        max_attempts,
        failure_reason,
        error_code,
        provider_reference,
        created_at,
        updated_at
    FROM fulfilment_audit
    {where}
    ORDER BY updated_at DESC
    LIMIT {limit_placeholder};
    """

    async with async_db_cursor() as cur:
        rows = await cur.fetch(query, *params)

    return {
        "status": "ok",
        "count": len(rows),
        "items": [dict(row) for row in rows],
    }


@router.post("/replay/{audit_id}")
async def replay_fulfilment(
    audit_id: str,
):
    result = await replay_failed_fulfilment(
        audit_id=audit_id,
    )

    return result

@router.get("/dashboard")
async def get_fulfilment_dashboard(
    tenant_code: str | None = Query(default=None),
):
    params = []
    where = ""

    if tenant_code:
        params.append(tenant_code)
        where = "WHERE tenant_code = $1"

    query = f"""
    SELECT
        COUNT(*) AS total_count,

        COUNT(*) FILTER (
            WHERE status = 'SUCCESS'
        ) AS success_count,

        COUNT(*) FILTER (
            WHERE status = 'FAILED_RETRYABLE'
        ) AS failed_retryable_count,

        COUNT(*) FILTER (
            WHERE status = 'FAILED_FINAL'
        ) AS failed_final_count,

        COUNT(*) FILTER (
            WHERE status = 'DLQ'
        ) AS dlq_count,

        COUNT(*) FILTER (
            WHERE status = 'SKIPPED_DUPLICATE'
        ) AS duplicate_skipped_count,

        COUNT(*) FILTER (
            WHERE status = 'PROCESSING'
        ) AS processing_count,

        COUNT(*) FILTER (
            WHERE status = 'PENDING'
        ) AS pending_count
    FROM fulfilment_audit
    {where};
    """

    async with async_db_cursor() as cur:
        row = await cur.fetchrow(query, *params)

    total_count = int(row["total_count"] or 0)
    success_count = int(row["success_count"] or 0)

    success_rate = (
        round((success_count / total_count) * 100, 2)
        if total_count > 0
        else 0.0
    )

    return {
        "status": "ok",
        "tenant_code": tenant_code,
        "summary": {
            "total_count": total_count,
            "success_count": success_count,
            "failed_retryable_count": int(row["failed_retryable_count"] or 0),
            "failed_final_count": int(row["failed_final_count"] or 0),
            "dlq_count": int(row["dlq_count"] or 0),
            "duplicate_skipped_count": int(row["duplicate_skipped_count"] or 0),
            "processing_count": int(row["processing_count"] or 0),
            "pending_count": int(row["pending_count"] or 0),
            "success_rate": success_rate,
        },
    }

@router.get("/providers/health")
async def get_all_provider_health(
    tenant_code: str | None = Query(default=None),
):
    items = await list_provider_health(
        tenant_code=tenant_code,
    )

    return {
        "status": "ok",
        "tenant_code": tenant_code,
        "count": len(items),
        "items": items,
    }


@router.get("/providers/{provider_key}/health")
async def get_single_provider_health(
    provider_key: str,
    tenant_code: str | None = Query(default=None),
):
    health = await get_provider_health(
        provider_key=provider_key,
        tenant_code=tenant_code,
    )

    return {
        "status": "ok",
        "health": health,
    }
