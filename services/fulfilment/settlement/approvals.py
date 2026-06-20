from __future__ import annotations

from typing import Any
from uuid import uuid4

from services.fulfilment.settlement.lock_enforcement import ensure_period_open
from utils.db import db_connection


APPROVAL_STATUS_PENDING = "PENDING"
APPROVAL_STATUS_APPROVED = "APPROVED"
APPROVAL_STATUS_REJECTED = "REJECTED"


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


def _period_projection(has_period_id: bool, alias: str | None = None) -> str:
    if has_period_id:
        return f"{alias}.period_id" if alias else "period_id"
    return "NULL::uuid AS period_id"


async def _ensure_batch_period_open(period_id: Any) -> None:
    if period_id is not None:
        await ensure_period_open(str(period_id))


async def request_batch_approval(
    *,
    batch_id: str,
    approval_type: str = "SETTLEMENT_BATCH_APPROVAL",
    requested_by: str,
    comments: str | None = None,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
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

        await _ensure_batch_period_open(batch["period_id"])

        if batch["status"] != "READY_FOR_APPROVAL":
            return None

        existing = await conn.fetchrow(
            """
            SELECT
                approval_id,
                batch_id,
                approval_type,
                approval_status,
                requested_by,
                approved_by,
                comments,
                created_at,
                approved_at
            FROM settlement_approvals
            WHERE batch_id = $1
              AND approval_status = 'PENDING'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            batch_id,
        )

        if existing:
            return dict(existing)

        row = await conn.fetchrow(
            """
            INSERT INTO settlement_approvals (
                approval_id,
                batch_id,
                approval_type,
                approval_status,
                requested_by,
                comments
            )
            VALUES ($1, $2, $3, 'PENDING', $4, $5)
            RETURNING
                approval_id,
                batch_id,
                approval_type,
                approval_status,
                requested_by,
                approved_by,
                comments,
                created_at,
                approved_at
            """,
            uuid4(),
            batch_id,
            approval_type,
            requested_by,
            comments,
        )

    return dict(row)


async def approve_batch_request(
    *,
    approval_id: str,
    approved_by: str,
    comments: str | None = None,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        existing = await conn.fetchrow(
            f"""
            SELECT
                a.approval_id,
                a.batch_id,
                {_period_projection(has_period_id, "b")}
            FROM settlement_approvals a
            JOIN settlement_batches b
              ON b.batch_id = a.batch_id
            WHERE a.approval_id = $1
              AND a.approval_status = 'PENDING'
            """,
            approval_id,
        )

        if not existing:
            return None

        await _ensure_batch_period_open(existing["period_id"])

        approval = await conn.fetchrow(
            """
            UPDATE settlement_approvals
            SET
                approval_status = 'APPROVED',
                approved_by = $2,
                comments = COALESCE($3, comments),
                approved_at = NOW()
            WHERE approval_id = $1
              AND approval_status = 'PENDING'
            RETURNING
                approval_id,
                batch_id,
                approval_type,
                approval_status,
                requested_by,
                approved_by,
                comments,
                created_at,
                approved_at
            """,
            approval_id,
            approved_by,
            comments,
        )

        if not approval:
            return None

        await conn.execute(
            """
            UPDATE settlement_batches
            SET
                status = 'APPROVED',
                approved_by = $2,
                approved_at = NOW()
            WHERE batch_id = $1
              AND status = 'READY_FOR_APPROVAL'
            """,
            approval["batch_id"],
            approved_by,
        )

    return dict(approval)


async def reject_batch_request(
    *,
    approval_id: str,
    rejected_by: str,
    comments: str | None = None,
) -> dict[str, Any] | None:
    rejection_comment = comments or f"Rejected by {rejected_by}"

    async with db_connection() as conn:
        has_period_id = await _has_batch_period_id(conn)
        existing = await conn.fetchrow(
            f"""
            SELECT
                a.approval_id,
                a.batch_id,
                {_period_projection(has_period_id, "b")}
            FROM settlement_approvals a
            JOIN settlement_batches b
              ON b.batch_id = a.batch_id
            WHERE a.approval_id = $1
              AND a.approval_status = 'PENDING'
            """,
            approval_id,
        )

        if not existing:
            return None

        await _ensure_batch_period_open(existing["period_id"])

        approval = await conn.fetchrow(
            """
            UPDATE settlement_approvals
            SET
                approval_status = 'REJECTED',
                approved_by = $2,
                comments = $3,
                approved_at = NOW()
            WHERE approval_id = $1
              AND approval_status = 'PENDING'
            RETURNING
                approval_id,
                batch_id,
                approval_type,
                approval_status,
                requested_by,
                approved_by,
                comments,
                created_at,
                approved_at
            """,
            approval_id,
            rejected_by,
            rejection_comment,
        )

        if not approval:
            return None

        await conn.execute(
            """
            UPDATE settlement_batches
            SET status = 'DRAFT'
            WHERE batch_id = $1
              AND status = 'READY_FOR_APPROVAL'
            """,
            approval["batch_id"],
        )

    return dict(approval)


async def get_batch_approvals(
    *,
    batch_id: str,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
                approval_id,
                batch_id,
                approval_type,
                approval_status,
                requested_by,
                approved_by,
                comments,
                created_at,
                approved_at
            FROM settlement_approvals
            WHERE batch_id = $1
            ORDER BY created_at DESC
            """,
            batch_id,
        )

    return [dict(row) for row in rows]
