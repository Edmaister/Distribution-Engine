from __future__ import annotations

from decimal import Decimal
from typing import Any
from services.fulfilment.settlement.lock_enforcement import ensure_period_open

from utils.db import db_connection


async def create_settlement_certification(
    *,
    tenant_code: str,
    period_id: str,
    expected_amount: Decimal,
    actual_amount: Decimal,
) -> dict[str, Any]:
    variance_amount = actual_amount - expected_amount

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO settlement_certifications (
                tenant_code,
                period_id,
                expected_amount,
                actual_amount,
                variance_amount,
                status
            )
            VALUES ($1,$2,$3,$4,$5,'PENDING')
            RETURNING *
            """,
            tenant_code,
            period_id,
            expected_amount,
            actual_amount,
            variance_amount,
        )

    return dict(row)


async def get_settlement_certification(
    certification_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM settlement_certifications
            WHERE certification_id = $1
            """,
            certification_id,
        )

    return dict(row) if row else None


async def list_settlement_certifications(
    *,
    tenant_code: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        if tenant_code:
            rows = await conn.fetch(
                """
                SELECT *
                FROM settlement_certifications
                WHERE tenant_code = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                tenant_code,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT *
                FROM settlement_certifications
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )

    return [dict(row) for row in rows]


async def certify_settlement_period(
    *,
    certification_id: str,
    certified_by: str,
    certification_notes: str | None = None,
) -> dict[str, Any] | None:
    certification = await get_settlement_certification(
        certification_id,
    )

    if not certification:
        return None

    await ensure_period_open(
        str(certification["period_id"])
    )

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE settlement_certifications
            SET
                status='CERTIFIED',
                certified_by=$2,
                certification_notes=$3,
                certified_at=NOW()
            WHERE certification_id=$1
            RETURNING *
            """,
            certification_id,
            certified_by,
            certification_notes,
        )

    return dict(row) if row else None