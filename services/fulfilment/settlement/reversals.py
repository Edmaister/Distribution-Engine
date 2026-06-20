from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import uuid4
from services.fulfilment.settlement.lock_enforcement import ensure_period_open

from utils.db import db_connection


REVERSAL_STATUS_REQUESTED = "REQUESTED"
REVERSAL_STATUS_APPROVED = "APPROVED"
REVERSAL_STATUS_EXECUTED = "EXECUTED"


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


async def create_settlement_reversal(
    *,
    settlement_id: str,
    tenant_code: str,
    reversal_reason: str,
    amount: Decimal | int | float | str,
    requested_by: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        settlement = await conn.fetchrow(
            """
            SELECT
                settlement_id,
                period_id
            FROM fulfilment_settlement_ledger
            WHERE settlement_id = $1
              AND tenant_code = $2
            """,
            settlement_id,
            tenant_code,
        )

        if not settlement:
            raise ValueError(
                f"Settlement not found: {settlement_id}"
            )

        if settlement["period_id"] is not None:
            await ensure_period_open(
                str(settlement["period_id"])
            )

        row = await conn.fetchrow(
            """
            INSERT INTO settlement_reversals (
                reversal_id,
                settlement_id,
                tenant_code,
                reversal_reason,
                amount,
                status,
                requested_by,
                correlation_id
            )
            VALUES ($1, $2, $3, $4, $5, 'REQUESTED', $6, $7)
            RETURNING
                reversal_id,
                settlement_id,
                tenant_code,
                reversal_reason,
                amount,
                status,
                requested_by,
                approved_by,
                correlation_id,
                created_at,
                approved_at,
                executed_at
            """,
            uuid4(),
            settlement_id,
            tenant_code,
            reversal_reason,
            _money(amount),
            requested_by,
            correlation_id,
        )

    return dict(row)


async def get_settlement_reversal(
    *,
    reversal_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                reversal_id,
                settlement_id,
                tenant_code,
                reversal_reason,
                amount,
                status,
                requested_by,
                approved_by,
                correlation_id,
                created_at,
                approved_at,
                executed_at
            FROM settlement_reversals
            WHERE reversal_id = $1
            """,
            reversal_id,
        )

    return dict(row) if row else None


async def list_settlement_reversals(
    *,
    tenant_code: str | None = None,
    settlement_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                reversal_id,
                settlement_id,
                tenant_code,
                reversal_reason,
                amount,
                status,
                requested_by,
                approved_by,
                correlation_id,
                created_at,
                approved_at,
                executed_at
            FROM settlement_reversals
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::uuid IS NULL OR settlement_id = $2)
              AND ($3::text IS NULL OR status = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            settlement_id,
            status,
            limit,
        )

    return [dict(row) for row in rows]


async def approve_settlement_reversal(
    *,
    reversal_id: str,
    approved_by: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE settlement_reversals
            SET
                status = 'APPROVED',
                approved_by = $2,
                approved_at = NOW()
            WHERE reversal_id = $1
              AND status = 'REQUESTED'
            RETURNING
                reversal_id,
                settlement_id,
                tenant_code,
                reversal_reason,
                amount,
                status,
                requested_by,
                approved_by,
                correlation_id,
                created_at,
                approved_at,
                executed_at
            """,
            reversal_id,
            approved_by,
        )

    return dict(row) if row else None


async def execute_settlement_reversal(
    *,
    reversal_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        reversal = await conn.fetchrow(
            """
            SELECT
                reversal_id,
                settlement_id,
                amount,
                status
            FROM settlement_reversals
            WHERE reversal_id = $1
            """,
            reversal_id,
        )

        if not reversal:
            return None

        if reversal["status"] != REVERSAL_STATUS_APPROVED:
            return None

        await conn.execute(
            """
            UPDATE fulfilment_settlement_ledger
            SET
                status = 'REVERSED',
                reversed_at = NOW()
            WHERE settlement_id = $1
            """,
            reversal["settlement_id"],
        )

        row = await conn.fetchrow(
            """
            UPDATE settlement_reversals
            SET
                status = 'EXECUTED',
                executed_at = NOW()
            WHERE reversal_id = $1
            RETURNING
                reversal_id,
                settlement_id,
                tenant_code,
                reversal_reason,
                amount,
                status,
                requested_by,
                approved_by,
                correlation_id,
                created_at,
                approved_at,
                executed_at
            """,
            reversal_id,
        )

    return dict(row) if row else None