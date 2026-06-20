from __future__ import annotations

from typing import Any
from uuid import uuid4

from utils.db import db_connection


PERIOD_STATUS_OPEN = "OPEN"
PERIOD_STATUS_CLOSED = "CLOSED"


async def create_settlement_period(
    *,
    tenant_code: str,
    period_code: str,
    period_start: str,
    period_end: str,
    created_by: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO settlement_periods (
                period_id,
                tenant_code,
                period_code,
                period_start,
                period_end,
                status,
                created_by
            )
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5,
                'OPEN',
                $6
            )
            RETURNING
                period_id,
                tenant_code,
                period_code,
                period_start,
                period_end,
                status,
                created_by,
                closed_by,
                created_at,
                closed_at
            """,
            uuid4(),
            tenant_code,
            period_code,
            period_start,
            period_end,
            created_by,
        )

    return dict(row)


async def get_settlement_period(
    *,
    period_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                period_id,
                tenant_code,
                period_code,
                period_start,
                period_end,
                status,
                created_by,
                closed_by,
                created_at,
                closed_at
            FROM settlement_periods
            WHERE period_id = $1
            """,
            period_id,
        )

    return dict(row) if row else None


async def get_current_open_period(
    *,
    tenant_code: str | None = None,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                period_id,
                tenant_code,
                period_code,
                period_start,
                period_end,
                status,
                created_by,
                closed_by,
                created_at,
                closed_at
            FROM settlement_periods
            WHERE status = 'OPEN'
              AND ($1::text IS NULL OR tenant_code = $1)
            ORDER BY period_start DESC
            LIMIT 1
            """,
            tenant_code,
        )

    return dict(row) if row else None


async def list_settlement_periods(
    *,
    tenant_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                period_id,
                tenant_code,
                period_code,
                period_start,
                period_end,
                status,
                created_by,
                closed_by,
                created_at,
                closed_at
            FROM settlement_periods
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR status = $2)
            ORDER BY period_start DESC
            LIMIT $3
            """,
            tenant_code,
            status,
            limit,
        )

    return [dict(row) for row in rows]


async def close_settlement_period(
    *,
    period_id: str,
    closed_by: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE settlement_periods
            SET
                status = 'CLOSED',
                closed_by = $2,
                closed_at = NOW()
            WHERE period_id = $1
              AND status = 'OPEN'
            RETURNING
                period_id,
                tenant_code,
                period_code,
                period_start,
                period_end,
                status,
                created_by,
                closed_by,
                created_at,
                closed_at
            """,
            period_id,
            closed_by,
        )

    return dict(row) if row else None


async def reopen_settlement_period(
    *,
    period_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE settlement_periods
            SET
                status = 'OPEN',
                closed_by = NULL,
                closed_at = NULL
            WHERE period_id = $1
              AND status = 'CLOSED'
            RETURNING
                period_id,
                tenant_code,
                period_code,
                period_start,
                period_end,
                status,
                created_by,
                closed_by,
                created_at,
                closed_at
            """,
            period_id,
        )

    return dict(row) if row else None