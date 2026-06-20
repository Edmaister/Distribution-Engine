from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from utils.db import db_connection


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


async def get_or_create_daily_exposure(
    *,
    tenant_code: str,
    account_id: UUID | str,
    exposure_date: date | None = None,
) -> dict[str, Any]:
    exposure_date = exposure_date or date.today()

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_exposure (
                tenant_code,
                account_id,
                exposure_date
            )
            VALUES ($1, $2, $3)
            ON CONFLICT (tenant_code, account_id, exposure_date)
            DO UPDATE SET updated_at = funding_exposure.updated_at
            RETURNING *
            """,
            tenant_code,
            account_id,
            exposure_date,
        )

    return _row_to_dict(row)  # type: ignore[return-value]


async def increase_reserved_exposure(
    *,
    tenant_code: str,
    account_id: UUID | str,
    amount: Decimal,
    exposure_date: date | None = None,
) -> dict[str, Any]:
    exposure_date = exposure_date or date.today()

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_exposure (
                tenant_code,
                account_id,
                exposure_date,
                reserved_amount
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (tenant_code, account_id, exposure_date)
            DO UPDATE SET
                reserved_amount = funding_exposure.reserved_amount + EXCLUDED.reserved_amount,
                updated_at = NOW()
            RETURNING *
            """,
            tenant_code,
            account_id,
            exposure_date,
            amount,
        )

    return _row_to_dict(row)  # type: ignore[return-value]


async def settle_exposure(
    *,
    tenant_code: str,
    account_id: UUID | str,
    amount: Decimal,
    exposure_date: date | None = None,
) -> dict[str, Any]:
    exposure_date = exposure_date or date.today()

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_exposure (
                tenant_code,
                account_id,
                exposure_date,
                settled_amount
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (tenant_code, account_id, exposure_date)
            DO UPDATE SET
                reserved_amount = GREATEST(funding_exposure.reserved_amount - EXCLUDED.settled_amount, 0),
                settled_amount = funding_exposure.settled_amount + EXCLUDED.settled_amount,
                updated_at = NOW()
            RETURNING *
            """,
            tenant_code,
            account_id,
            exposure_date,
            amount,
        )

    return _row_to_dict(row)  # type: ignore[return-value]


async def release_exposure(
    *,
    tenant_code: str,
    account_id: UUID | str,
    amount: Decimal,
    exposure_date: date | None = None,
) -> dict[str, Any]:
    exposure_date = exposure_date or date.today()

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_exposure (
                tenant_code,
                account_id,
                exposure_date,
                released_amount
            )
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (tenant_code, account_id, exposure_date)
            DO UPDATE SET
                reserved_amount = GREATEST(funding_exposure.reserved_amount - EXCLUDED.released_amount, 0),
                released_amount = funding_exposure.released_amount + EXCLUDED.released_amount,
                updated_at = NOW()
            RETURNING *
            """,
            tenant_code,
            account_id,
            exposure_date,
            amount,
        )

    return _row_to_dict(row)  # type: ignore[return-value]


async def list_funding_exposure(
    *,
    tenant_code: str | None = None,
    account_id: UUID | str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_exposure
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::uuid IS NULL OR account_id = $2)
            ORDER BY exposure_date DESC, updated_at DESC
            LIMIT $3
            """,
            tenant_code,
            account_id,
            limit,
        )

    return [dict(row) for row in rows]