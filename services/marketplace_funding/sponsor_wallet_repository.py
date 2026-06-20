from __future__ import annotations

from decimal import Decimal
from typing import Any

from utils.db import db_connection


async def create_wallet(
    *,
    tenant_code: str,
    sponsor_code: str,
    sponsor_name: str,
    currency: str = "ZAR",
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_wallets (
            tenant_code,
            sponsor_code,
            sponsor_name,
            currency
        )
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (tenant_code, sponsor_code, currency)
        DO UPDATE SET
            sponsor_name = EXCLUDED.sponsor_name,
            updated_at = NOW()
        RETURNING
            wallet_id,
            tenant_code,
            sponsor_code,
            sponsor_name,
            currency,
            current_balance,
            reserved_balance,
            status,
            created_at,
            updated_at;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            tenant_code,
            sponsor_code,
            sponsor_name,
            currency,
        )

    return dict(row)


async def get_wallet(
    *,
    wallet_id: str,
) -> dict[str, Any] | None:
    query = """
        SELECT
            wallet_id,
            tenant_code,
            sponsor_code,
            sponsor_name,
            currency,
            current_balance,
            reserved_balance,
            status,
            created_at,
            updated_at
        FROM sponsor_wallets
        WHERE wallet_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, wallet_id)

    return dict(row) if row else None


async def get_wallet_by_sponsor(
    *,
    tenant_code: str,
    sponsor_code: str,
    currency: str = "ZAR",
) -> dict[str, Any] | None:
    query = """
        SELECT
            wallet_id,
            tenant_code,
            sponsor_code,
            sponsor_name,
            currency,
            current_balance,
            reserved_balance,
            status,
            created_at,
            updated_at
        FROM sponsor_wallets
        WHERE tenant_code = $1
          AND sponsor_code = $2
          AND currency = $3;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            tenant_code,
            sponsor_code,
            currency,
        )

    return dict(row) if row else None


async def list_wallets(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            wallet_id,
            tenant_code,
            sponsor_code,
            sponsor_name,
            currency,
            current_balance,
            reserved_balance,
            status,
            created_at,
            updated_at
        FROM sponsor_wallets
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


async def update_wallet_balances(
    *,
    wallet_id: str,
    current_balance: Decimal,
    reserved_balance: Decimal,
) -> dict[str, Any] | None:
    query = """
        UPDATE sponsor_wallets
        SET
            current_balance = $1,
            reserved_balance = $2,
            updated_at = NOW()
        WHERE wallet_id = $3
        RETURNING
            wallet_id,
            tenant_code,
            sponsor_code,
            sponsor_name,
            currency,
            current_balance,
            reserved_balance,
            status,
            created_at,
            updated_at;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            current_balance,
            reserved_balance,
            wallet_id,
        )

    return dict(row) if row else None