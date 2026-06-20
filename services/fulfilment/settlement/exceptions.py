from __future__ import annotations

from typing import Any
from uuid import uuid4

from utils.db import db_connection


EXCEPTION_STATUS_OPEN = "OPEN"
EXCEPTION_STATUS_RESOLVED = "RESOLVED"

SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_CRITICAL = "CRITICAL"


async def create_settlement_exception(
    *,
    exception_type: str,
    severity: str,
    exception_message: str | None = None,
    batch_id: str | None = None,
    settlement_id: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO settlement_exceptions (
                exception_id,
                batch_id,
                settlement_id,
                exception_type,
                severity,
                status,
                exception_message,
                correlation_id
            )
            VALUES ($1, $2, $3, $4, $5, 'OPEN', $6, $7)
            RETURNING
                exception_id,
                batch_id,
                settlement_id,
                exception_type,
                severity,
                status,
                exception_message,
                correlation_id,
                created_at,
                resolved_at,
                resolved_by
            """,
            uuid4(),
            batch_id,
            settlement_id,
            exception_type,
            severity,
            exception_message,
            correlation_id,
        )

    return dict(row)


async def list_settlement_exceptions(
    *,
    batch_id: str | None = None,
    settlement_id: str | None = None,
    status: str | None = EXCEPTION_STATUS_OPEN,
    severity: str | None = None,
    exception_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                exception_id,
                batch_id,
                settlement_id,
                exception_type,
                severity,
                status,
                exception_message,
                correlation_id,
                created_at,
                resolved_at,
                resolved_by
            FROM settlement_exceptions
            WHERE ($1::uuid IS NULL OR batch_id = $1)
              AND ($2::uuid IS NULL OR settlement_id = $2)
              AND ($3::text IS NULL OR status = $3)
              AND ($4::text IS NULL OR severity = $4)
              AND ($5::text IS NULL OR exception_type = $5)
            ORDER BY created_at DESC
            LIMIT $6
            """,
            batch_id,
            settlement_id,
            status,
            severity,
            exception_type,
            limit,
        )

    return [dict(row) for row in rows]


async def get_settlement_exception(
    *,
    exception_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                exception_id,
                batch_id,
                settlement_id,
                exception_type,
                severity,
                status,
                exception_message,
                correlation_id,
                created_at,
                resolved_at,
                resolved_by
            FROM settlement_exceptions
            WHERE exception_id = $1
            """,
            exception_id,
        )

    return dict(row) if row else None


async def resolve_settlement_exception(
    *,
    exception_id: str,
    resolved_by: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE settlement_exceptions
            SET
                status = 'RESOLVED',
                resolved_at = NOW(),
                resolved_by = $2
            WHERE exception_id = $1
              AND status = 'OPEN'
            RETURNING
                exception_id,
                batch_id,
                settlement_id,
                exception_type,
                severity,
                status,
                exception_message,
                correlation_id,
                created_at,
                resolved_at,
                resolved_by
            """,
            exception_id,
            resolved_by,
        )

    return dict(row) if row else None