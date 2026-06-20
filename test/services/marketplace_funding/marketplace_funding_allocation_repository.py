# repositories/marketplace_funding_allocation_repository.py

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from utils.db import db_connection


async def create_funding_allocation(
    *,
    reward_id: str,
    wallet_id: str,
    tenant_code: str,
    sponsor_code: str,
    amount: Decimal,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO marketplace_funding_allocations (
            reward_id,
            wallet_id,
            tenant_code,
            sponsor_code,
            amount,
            status,
            correlation_id,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, 'RESERVED', $6, $7::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            reward_id,
            wallet_id,
            tenant_code,
            sponsor_code,
            amount,
            correlation_id,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def get_funding_allocation_by_reward(
    *,
    reward_id: str,
) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM marketplace_funding_allocations
        WHERE reward_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, reward_id)

    return dict(row) if row else None


async def get_funding_allocation_by_id(
    *,
    allocation_id: str,
) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM marketplace_funding_allocations
        WHERE allocation_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, allocation_id)

    return dict(row) if row else None


async def mark_allocation_released(
    *,
    allocation_id: str,
) -> dict[str, Any] | None:
    query = """
        UPDATE marketplace_funding_allocations
        SET
            status = 'RELEASED',
            released_at = now(),
            updated_at = now()
        WHERE allocation_id = $1
          AND status = 'RESERVED'
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, allocation_id)

    return dict(row) if row else None


async def mark_allocation_debited(
    *,
    allocation_id: str,
) -> dict[str, Any] | None:
    query = """
        UPDATE marketplace_funding_allocations
        SET
            status = 'DEBITED',
            debited_at = now(),
            updated_at = now()
        WHERE allocation_id = $1
          AND status = 'RESERVED'
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, allocation_id)

    return dict(row) if row else None


async def mark_allocation_reversed(
    *,
    allocation_id: str,
) -> dict[str, Any] | None:
    query = """
        UPDATE marketplace_funding_allocations
        SET
            status = 'REVERSED',
            reversed_at = now(),
            updated_at = now()
        WHERE allocation_id = $1
          AND status = 'DEBITED'
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, allocation_id)

    return dict(row) if row else None


async def list_funding_allocations(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM marketplace_funding_allocations
        WHERE tenant_code = $1
          AND ($2::text IS NULL OR sponsor_code = $2)
          AND ($3::text IS NULL OR status = $3)
        ORDER BY created_at DESC
        LIMIT $4;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(
            query,
            tenant_code,
            sponsor_code,
            status,
            limit,
        )

    return [dict(row) for row in rows]