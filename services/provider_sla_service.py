from __future__ import annotations

from typing import Any

from utils.db import db_connection


async def record_provider_success(
    *,
    provider_key: str,
    latency_ms: int,
) -> None:
    async with db_connection() as conn:
        await conn.execute(
            """
            INSERT INTO provider_sla_metrics (
                provider_key,
                success_count,
                total_latency_ms
            )
            VALUES ($1, 1, $2)
            ON CONFLICT (provider_key)
            DO UPDATE SET
                success_count = provider_sla_metrics.success_count + 1,
                total_latency_ms = provider_sla_metrics.total_latency_ms + $2,
                updated_at = NOW()
            """,
            provider_key,
            latency_ms,
        )


async def record_provider_failure(
    *,
    provider_key: str,
    latency_ms: int,
) -> None:
    async with db_connection() as conn:
        await conn.execute(
            """
            INSERT INTO provider_sla_metrics (
                provider_key,
                failure_count,
                total_latency_ms
            )
            VALUES ($1, 1, $2)
            ON CONFLICT (provider_key)
            DO UPDATE SET
                failure_count = provider_sla_metrics.failure_count + 1,
                total_latency_ms = provider_sla_metrics.total_latency_ms + $2,
                updated_at = NOW()
            """,
            provider_key,
            latency_ms,
        )


async def record_provider_retry(
    *,
    provider_key: str,
) -> None:
    async with db_connection() as conn:
        await conn.execute(
            """
            INSERT INTO provider_sla_metrics (
                provider_key,
                retry_count
            )
            VALUES ($1, 1)
            ON CONFLICT (provider_key)
            DO UPDATE SET
                retry_count = provider_sla_metrics.retry_count + 1,
                updated_at = NOW()
            """,
            provider_key,
        )


async def get_provider_sla_metrics(
    *,
    provider_key: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM provider_sla_metrics
            WHERE provider_key = $1
            """,
            provider_key,
        )

    return dict(row) if row else None


async def list_provider_sla_metrics(
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM provider_sla_metrics
            ORDER BY updated_at DESC
            LIMIT $1
            """,
            limit,
        )

    return [dict(row) for row in rows]