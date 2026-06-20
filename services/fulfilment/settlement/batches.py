from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import uuid4

from services.fulfilment.settlement.lock_enforcement import ensure_period_open
from utils.db import db_connection


BATCH_STATUS_DRAFT = "DRAFT"
BATCH_STATUS_READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
BATCH_STATUS_APPROVED = "APPROVED"
BATCH_STATUS_PROCESSING = "PROCESSING"
BATCH_STATUS_SETTLED = "SETTLED"

ITEM_STATUS_ADDED = "ADDED"
ITEM_STATUS_SETTLED = "SETTLED"


async def _has_batch_period_id(conn) -> bool:
    return bool(
        await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'settlement_batches'
                  AND column_name = 'period_id'
            )
            """
        )
    )


def _period_projection(has_period_id: bool) -> str:
    return "period_id" if has_period_id else "NULL::uuid AS period_id"


def _batch_returning_columns(has_period_id: bool) -> str:
    return f"""
                batch_id,
                tenant_code,
                batch_reference,
                batch_type,
                status,
                total_count,
                total_amount,
                created_by,
                approved_by,
                created_at,
                approved_at,
                settled_at,
                {_period_projection(has_period_id)}
            """


def _money(value: Any) -> Decimal:
    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


async def create_settlement_batch(
    *,
    tenant_code: str,
    batch_reference: str,
    batch_type: str = "REWARD_SETTLEMENT",
    created_by: str | None = None,
    period_id: str | None = None,
) -> dict[str, Any]:
    if period_id is not None:
        await ensure_period_open(str(period_id))

    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        returning_columns = _batch_returning_columns(has_period_id)
        if has_period_id:
            row = await conn.fetchrow(
                f"""
                INSERT INTO settlement_batches (
                    batch_id,
                    tenant_code,
                    batch_reference,
                    batch_type,
                    status,
                    total_count,
                    total_amount,
                    created_by,
                    period_id
                )
                VALUES ($1, $2, $3, $4, 'DRAFT', 0, 0, $5, $6)
                RETURNING
                    {returning_columns}
                """,
                uuid4(),
                tenant_code,
                batch_reference,
                batch_type,
                created_by,
                period_id,
            )
        else:
            row = await conn.fetchrow(
                f"""
                INSERT INTO settlement_batches (
                    batch_id,
                    tenant_code,
                    batch_reference,
                    batch_type,
                    status,
                    total_count,
                    total_amount,
                    created_by
                )
                VALUES ($1, $2, $3, $4, 'DRAFT', 0, 0, $5)
                RETURNING
                    {returning_columns}
                """,
                uuid4(),
                tenant_code,
                batch_reference,
                batch_type,
                created_by,
            )

    return dict(row)


async def add_settlement_to_batch(
    *,
    batch_id: str,
    settlement_id: str,
    amount: Decimal | int | float | str,
) -> dict[str, Any] | None:
    amount_value = _money(amount)

    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        returning_columns = _batch_returning_columns(has_period_id)
        batch = await conn.fetchrow(
            f"""
            SELECT batch_id, status, {_period_projection(has_period_id)}
            FROM settlement_batches
            WHERE batch_id = $1
            """,
            batch_id,
        )

        if not batch:
            return None

        if batch["period_id"] is not None:
            await ensure_period_open(str(batch["period_id"]))

        if batch["status"] != BATCH_STATUS_DRAFT:
            return None

        item = await conn.fetchrow(
            """
            INSERT INTO settlement_batch_items (
                batch_item_id,
                batch_id,
                settlement_id,
                amount,
                status
            )
            VALUES ($1, $2, $3, $4, 'ADDED')
            RETURNING
                batch_item_id,
                batch_id,
                settlement_id,
                amount,
                status,
                created_at
            """,
            uuid4(),
            batch_id,
            settlement_id,
            amount_value,
        )

        updated_batch = await conn.fetchrow(
            f"""
            UPDATE settlement_batches
            SET
                total_count = total_count + 1,
                total_amount = total_amount + $2
            WHERE batch_id = $1
            RETURNING
                {returning_columns}
            """,
            batch_id,
            amount_value,
        )

    return {
        "item": dict(item),
        "batch": dict(updated_batch),
    }


async def submit_batch_for_approval(
    *,
    batch_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        returning_columns = _batch_returning_columns(has_period_id)
        batch = await conn.fetchrow(
            f"""
            SELECT batch_id, status, {_period_projection(has_period_id)}
            FROM settlement_batches
            WHERE batch_id = $1
            """,
            batch_id,
        )

        if not batch:
            return None

        if batch["period_id"] is not None:
            await ensure_period_open(str(batch["period_id"]))

        row = await conn.fetchrow(
            f"""
            UPDATE settlement_batches
            SET status = 'READY_FOR_APPROVAL'
            WHERE batch_id = $1
              AND status = 'DRAFT'
              AND total_count > 0
            RETURNING
                {returning_columns}
            """,
            batch_id,
        )

    return dict(row) if row else None


async def approve_batch(
    *,
    batch_id: str,
    approved_by: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        returning_columns = _batch_returning_columns(has_period_id)
        batch = await conn.fetchrow(
            f"""
            SELECT batch_id, status, {_period_projection(has_period_id)}
            FROM settlement_batches
            WHERE batch_id = $1
            """,
            batch_id,
        )

        if not batch:
            return None

        if batch["period_id"] is not None:
            await ensure_period_open(str(batch["period_id"]))

        row = await conn.fetchrow(
            f"""
            UPDATE settlement_batches
            SET
                status = 'APPROVED',
                approved_by = $2,
                approved_at = NOW()
            WHERE batch_id = $1
              AND status = 'READY_FOR_APPROVAL'
            RETURNING
                {returning_columns}
            """,
            batch_id,
            approved_by,
        )

    return dict(row) if row else None


async def execute_batch(
    *,
    batch_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        returning_columns = _batch_returning_columns(has_period_id)
        existing = await conn.fetchrow(
            f"""
            SELECT batch_id, status, {_period_projection(has_period_id)}
            FROM settlement_batches
            WHERE batch_id = $1
            """,
            batch_id,
        )

        if not existing:
            return None

        if existing["period_id"] is not None:
            await ensure_period_open(str(existing["period_id"]))

        batch = await conn.fetchrow(
            """
            UPDATE settlement_batches
            SET status = 'PROCESSING'
            WHERE batch_id = $1
              AND status = 'APPROVED'
            RETURNING batch_id
            """,
            batch_id,
        )

        if not batch:
            return None

        await conn.execute(
            """
            UPDATE settlement_batch_items
            SET status = 'SETTLED'
            WHERE batch_id = $1
              AND status = 'ADDED'
            """,
            batch_id,
        )

        row = await conn.fetchrow(
            f"""
            UPDATE settlement_batches
            SET
                status = 'SETTLED',
                settled_at = NOW()
            WHERE batch_id = $1
            RETURNING
                {returning_columns}
            """,
            batch_id,
        )

    return dict(row) if row else None


async def get_settlement_batch(
    *,
    batch_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        returning_columns = _batch_returning_columns(has_period_id)
        batch = await conn.fetchrow(
            f"""
            SELECT
                {returning_columns}
            FROM settlement_batches
            WHERE batch_id = $1
            """,
            batch_id,
        )

        if not batch:
            return None

        items = await conn.fetch(
            """
            SELECT
                batch_item_id,
                batch_id,
                settlement_id,
                amount,
                status,
                created_at
            FROM settlement_batch_items
            WHERE batch_id = $1
            ORDER BY created_at ASC
            """,
            batch_id,
        )

    return {
        "batch": dict(batch),
        "item_count": len(items),
        "items": [dict(item) for item in items],
    }


async def list_settlement_batches(
    *,
    tenant_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        returning_columns = _batch_returning_columns(has_period_id)
        rows = await conn.fetch(
            f"""
            SELECT
                {returning_columns}
            FROM settlement_batches
            WHERE ($1::text IS NULL OR tenant_code = $1)
              AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
            LIMIT $3
            """,
            tenant_code,
            status,
            limit,
        )

    return [dict(row) for row in rows]
