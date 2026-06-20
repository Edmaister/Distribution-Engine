from __future__ import annotations
import json
from datetime import date
from decimal import Decimal
from typing import Any

from utils.db import db_connection


async def create_contract(
    *,
    tenant_code: str,
    sponsor_code: str,
    sponsor_name: str,
    contract_name: str,
    contract_value: Decimal,
    start_date: date,
    end_date: date,
    currency: str = "ZAR",
    status: str = "ACTIVE",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO funding_contracts (
            tenant_code,
            sponsor_code,
            sponsor_name,
            contract_name,
            contract_value,
            committed_amount,
            utilised_amount,
            remaining_amount,
            start_date,
            end_date,
            status
        )
        VALUES (
            $1, $2, $3, $4, $5,
            0, 0, $5,
            $6, $7, $8
        )
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            tenant_code,
            sponsor_code,
            sponsor_name,
            contract_name,
            contract_value,
            start_date,
            end_date,
            status,
        )

    return dict(row)


async def get_contract(
    *,
    contract_id: str,
) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM funding_contracts
        WHERE contract_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, contract_id)

    return dict(row) if row else None


async def list_contracts(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM funding_contracts
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


async def get_active_contract_for_sponsor(
    *,
    tenant_code: str,
    sponsor_code: str,
    as_of_date: date,
) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM funding_contracts
        WHERE tenant_code = $1
          AND sponsor_code = $2
          AND status = 'ACTIVE'
          AND start_date <= $3
          AND end_date >= $3
        ORDER BY end_date ASC
        LIMIT 1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            tenant_code,
            sponsor_code,
            as_of_date,
        )

    return dict(row) if row else None


async def update_contract_status(
    *,
    contract_id: str,
    status: str,
) -> dict[str, Any] | None:
    query = """
        UPDATE funding_contracts
        SET status = $2,
            updated_at = NOW()
        WHERE contract_id = $1
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, contract_id, status)

    return dict(row) if row else None


async def commit_contract_amount(
    *,
    contract_id: str,
    amount: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE funding_contracts
        SET committed_amount = committed_amount + $2,
            remaining_amount = remaining_amount - $2,
            updated_at = NOW()
        WHERE contract_id = $1
          AND remaining_amount >= $2
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, contract_id, amount)

    return dict(row) if row else None


async def release_contract_amount(
    *,
    contract_id: str,
    amount: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE funding_contracts
        SET committed_amount = committed_amount - $2,
            remaining_amount = remaining_amount + $2,
            updated_at = NOW()
        WHERE contract_id = $1
          AND committed_amount >= $2
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, contract_id, amount)

    return dict(row) if row else None


async def utilise_contract_amount(
    *,
    contract_id: str,
    amount: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE funding_contracts
        SET committed_amount = committed_amount - $2,
            utilised_amount = utilised_amount + $2,
            updated_at = NOW()
        WHERE contract_id = $1
          AND committed_amount >= $2
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, contract_id, amount)

    return dict(row) if row else None


async def create_contract_ledger_entry(
    *,
    contract_id: str,
    event_type: str,
    amount: Decimal,
    reward_id: str | None = None,
    allocation_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO funding_contract_ledger (
            contract_id,
            event_type,
            amount,
            reward_id,
            allocation_id,
            correlation_id,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
        RETURNING *;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            contract_id,
            event_type,
            amount,
            reward_id,
            allocation_id,
            correlation_id,
            json.dumps(metadata or {}),
        )

    return dict(row)


async def list_contract_ledger(
    *,
    contract_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM funding_contract_ledger
        WHERE contract_id = $1
        ORDER BY created_at DESC
        LIMIT $2;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, contract_id, limit)

    return [dict(row) for row in rows]