from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from utils.db import db_connection


def _serialize_row(row: Any) -> dict[str, Any]:
    result = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }

    if isinstance(result.get("metadata"), str):
        result["metadata"] = json.loads(result["metadata"])

    return result


async def create_ledger_entry(
    *,
    wallet_id: str,
    tenant_code: str,
    transaction_type: str,
    amount: Decimal,
    balance_before: Decimal,
    balance_after: Decimal,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO sponsor_wallet_ledger (
            wallet_id,
            tenant_code,
            transaction_type,
            amount,
            balance_before,
            balance_after,
            correlation_id,
            metadata
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
        RETURNING
            ledger_id,
            wallet_id,
            tenant_code,
            transaction_type,
            amount,
            balance_before,
            balance_after,
            correlation_id,
            metadata,
            created_at;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(
            query,
            wallet_id,
            tenant_code,
            transaction_type,
            amount,
            balance_before,
            balance_after,
            correlation_id,
            json.dumps(metadata or {}),
        )

    return _serialize_row(row)


async def list_wallet_ledger(
    *,
    wallet_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT
            ledger_id,
            wallet_id,
            tenant_code,
            transaction_type,
            amount,
            balance_before,
            balance_after,
            correlation_id,
            metadata,
            created_at
        FROM sponsor_wallet_ledger
        WHERE wallet_id = $1
        ORDER BY created_at DESC
        LIMIT $2;
    """

    async with db_connection() as conn:
        rows = await conn.fetch(query, wallet_id, limit)

    return [_serialize_row(row) for row in rows]