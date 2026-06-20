from __future__ import annotations

from typing import Any

from services.reconciliation_exception_status import (
    ReconciliationExceptionStatus,
)
from utils.db import db_connection


async def create_exception(
    *,
    run_id: str,
    provider_reference: str | None,
    exception_type: str,
) -> dict[str, Any]:

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO reconciliation_exceptions (
                run_id,
                provider_reference,
                exception_type
            )
            VALUES (
                $1,$2,$3
            )
            RETURNING *
            """,
            run_id,
            provider_reference,
            exception_type,
        )

    return dict(row)


async def assign_exception(
    *,
    exception_id: str,
    assigned_to: str,
) -> dict[str, Any]:

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE reconciliation_exceptions
            SET
                assigned_to = $1,
                status = $2,
                updated_at = NOW()
            WHERE exception_id = $3
            RETURNING *
            """,
            assigned_to,
            ReconciliationExceptionStatus.ASSIGNED.value,
            exception_id,
        )

    return dict(row) if row else None


async def resolve_exception(
    *,
    exception_id: str,
    resolution_notes: str,
) -> dict[str, Any]:

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE reconciliation_exceptions
            SET
                status = $1,
                resolution_notes = $2,
                resolved_at = NOW(),
                updated_at = NOW()
            WHERE exception_id = $3
            RETURNING *
            """,
            ReconciliationExceptionStatus.RESOLVED.value,
            resolution_notes,
            exception_id,
        )

    return dict(row) if row else None


async def reopen_exception(
    *,
    exception_id: str,
) -> dict[str, Any]:

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE reconciliation_exceptions
            SET
                status = $1,
                resolved_at = NULL,
                updated_at = NOW()
            WHERE exception_id = $2
            RETURNING *
            """,
            ReconciliationExceptionStatus.REOPENED.value,
            exception_id,
        )

    return dict(row) if row else None


async def get_exception(
    *,
    exception_id: str,
) -> dict[str, Any] | None:

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM reconciliation_exceptions
            WHERE exception_id = $1
            """,
            exception_id,
        )

    return dict(row) if row else None


async def list_exceptions(
    *,
    status: str | None = None,
    assigned_to: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:

    filters = []
    params: list[Any] = []

    if status:
        params.append(status)
        filters.append(f"status = ${len(params)}")

    if assigned_to:
        params.append(assigned_to)
        filters.append(f"assigned_to = ${len(params)}")

    params.append(limit)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT *
            FROM reconciliation_exceptions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
            """,
            *params,
        )

    return [dict(row) for row in rows]