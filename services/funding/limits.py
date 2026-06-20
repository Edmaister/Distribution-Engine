from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from utils.db import db_connection


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


async def create_funding_limit(
    *,
    tenant_code: str,
    account_id: UUID | str,
    daily_limit: Decimal,
    monthly_limit: Decimal,
    exposure_limit: Decimal,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_limits (
                tenant_code,
                account_id,
                daily_limit,
                monthly_limit,
                exposure_limit,
                is_active
            )
            VALUES ($1, $2, $3, $4, $5, TRUE)
            RETURNING *
            """,
            tenant_code,
            account_id,
            daily_limit,
            monthly_limit,
            exposure_limit,
        )

    return _row_to_dict(row)  # type: ignore[return-value]


async def update_funding_limit(
    *,
    limit_id: UUID | str,
    daily_limit: Decimal | None = None,
    monthly_limit: Decimal | None = None,
    exposure_limit: Decimal | None = None,
    is_active: bool | None = None,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_limits
            SET
                daily_limit = COALESCE($2, daily_limit),
                monthly_limit = COALESCE($3, monthly_limit),
                exposure_limit = COALESCE($4, exposure_limit),
                is_active = COALESCE($5, is_active),
                updated_at = NOW()
            WHERE limit_id = $1
            RETURNING *
            """,
            limit_id,
            daily_limit,
            monthly_limit,
            exposure_limit,
            is_active,
        )

    return _row_to_dict(row)


async def get_active_funding_limit(
    *,
    tenant_code: str,
    account_id: UUID | str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM funding_limits
            WHERE tenant_code = $1
              AND account_id = $2
              AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            tenant_code,
            account_id,
        )

    return _row_to_dict(row)


async def list_funding_limits(
    *,
    tenant_code: str | None = None,
    account_id: UUID | str | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_limits
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::uuid IS NULL OR account_id = $2)
              AND ($3::boolean IS FALSE OR is_active = TRUE)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            account_id,
            active_only,
            limit,
        )

    return [dict(row) for row in rows]