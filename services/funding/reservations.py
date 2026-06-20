from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from utils.db import db_connection


class FundingReservationError(Exception):
    """Base funding reservation error."""


class FundingReservationNotFound(FundingReservationError):
    """Raised when a reservation cannot be found."""


class InvalidReservationStatus(FundingReservationError):
    """Raised when a reservation is in the wrong status."""


async def create_funding_reservation(
    *,
    reward_id: str,
    tenant_code: str,
    account_id: UUID | str,
    amount: Decimal,
    funding_transaction_id: UUID | str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    reservation_id = uuid4()

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_reservations (
                reservation_id,
                reward_id,
                tenant_code,
                account_id,
                amount,
                funding_transaction_id,
                status,
                correlation_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, 'RESERVED', $7)
            RETURNING *
            """,
            reservation_id,
            reward_id,
            tenant_code,
            UUID(str(account_id)),
            amount,
            UUID(str(funding_transaction_id)),
            correlation_id,
        )

    return dict(row)


async def get_funding_reservation_by_reward(
    *,
    reward_id: str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM funding_reservations
            WHERE reward_id = $1
            """,
            reward_id,
        )

    return dict(row) if row else None


async def get_funding_reservation(
    *,
    reservation_id: UUID | str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM funding_reservations
            WHERE reservation_id = $1
            """,
            UUID(str(reservation_id)),
        )

    return dict(row) if row else None


async def mark_reservation_released(
    *,
    reward_id: str,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_reservations
            SET status = 'RELEASED',
                updated_at = NOW()
            WHERE reward_id = $1
              AND status = 'RESERVED'
            RETURNING *
            """,
            reward_id,
        )

    if not row:
        raise FundingReservationNotFound("Reserved funding reservation not found")

    return dict(row)


async def mark_reservation_settled(
    *,
    reward_id: str,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE funding_reservations
            SET status = 'SETTLED',
                updated_at = NOW()
            WHERE reward_id = $1
              AND status = 'RESERVED'
            RETURNING *
            """,
            reward_id,
        )

    if not row:
        raise FundingReservationNotFound("Reserved funding reservation not found")

    return dict(row)


async def list_funding_reservations(
    *,
    tenant_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_reservations
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