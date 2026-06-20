from __future__ import annotations

from typing import Any

from services.fulfilment_circuit_breaker_service import (
    get_circuit_snapshot,
)
from utils.db import async_db_cursor


async def get_provider_health(
    *,
    provider_key: str,
    tenant_code: str | None = None,
) -> dict[str, Any]:
    params = [provider_key]
    where = "WHERE fulfilment_provider = $1"

    if tenant_code:
        params.append(tenant_code)
        where += f" AND tenant_code = ${len(params)}"

    query = f"""
    SELECT
        COUNT(*) AS total_count,

        COUNT(*) FILTER (
            WHERE status = 'SUCCESS'
        ) AS success_count,

        COUNT(*) FILTER (
            WHERE status IN ('FAILED_RETRYABLE', 'FAILED_FINAL', 'DLQ')
        ) AS failure_count,

        COUNT(*) FILTER (
            WHERE status = 'FAILED_RETRYABLE'
        ) AS retryable_failure_count,

        COUNT(*) FILTER (
            WHERE status = 'DLQ'
        ) AS dlq_count,

        MAX(completed_at) AS last_success_at,

        MAX(failed_at) AS last_failure_at
    FROM fulfilment_audit
    {where};
    """

    async with async_db_cursor() as cur:
        row = await cur.fetchrow(query, *params)

    total_count = int(row["total_count"] or 0)
    success_count = int(row["success_count"] or 0)
    failure_count = int(row["failure_count"] or 0)

    success_rate = (
        round((success_count / total_count) * 100, 2)
        if total_count > 0
        else 0.0
    )

    failure_rate = (
        round((failure_count / total_count) * 100, 2)
        if total_count > 0
        else 0.0
    )

    return {
        "provider_key": provider_key,
        "tenant_code": tenant_code,
        "total_count": total_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "retryable_failure_count": int(row["retryable_failure_count"] or 0),
        "dlq_count": int(row["dlq_count"] or 0),
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "last_success_at": (
            row["last_success_at"].isoformat()
            if row["last_success_at"]
            else None
        ),
        "last_failure_at": (
            row["last_failure_at"].isoformat()
            if row["last_failure_at"]
            else None
        ),
        "circuit": get_circuit_snapshot(provider_key),
    }


async def list_provider_health(
    *,
    tenant_code: str | None = None,
) -> list[dict[str, Any]]:
    params = []
    where = ""

    if tenant_code:
        params.append(tenant_code)
        where = "WHERE tenant_code = $1"

    query = f"""
    SELECT DISTINCT fulfilment_provider
    FROM fulfilment_audit
    {where}
    ORDER BY fulfilment_provider;
    """

    async with async_db_cursor() as cur:
        rows = await cur.fetch(query, *params)

    return [
        await get_provider_health(
            provider_key=row["fulfilment_provider"],
            tenant_code=tenant_code,
        )
        for row in rows
    ]