# services/marketplace_funding/sponsor_funding_service.py

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID

from services.marketplace_funding.sponsor_wallet_balance_service import (
    debit_wallet,
    release_wallet_reservation,
    reserve_wallet_funds,
)
from utils.db import db_connection


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _serialize_row(row: Any) -> dict[str, Any]:
    data = dict(row)
    return {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in data.items()
    }


async def get_allocation_by_reward(*, reward_id: str) -> dict[str, Any] | None:
    try:
        UUID(str(reward_id))
    except (ValueError, TypeError):
        return None

    query = """
        SELECT *
        FROM marketplace_funding_allocations
        WHERE reward_id = $1;
    """

    async with db_connection() as conn:
        row = await conn.fetchrow(query, reward_id)

    return _serialize_row(row) if row else None


async def get_allocation_by_id(*, allocation_id: str) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM marketplace_funding_allocations
        WHERE allocation_id = $1;
    """
    async with db_connection() as conn:
        row = await conn.fetchrow(query, allocation_id)

    return _serialize_row(row) if row else None


async def create_allocation(
    *,
    reward_id: str,
    wallet_id: str,
    tenant_code: str,
    sponsor_code: str,
    amount: Decimal | int | float | str,
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
            _to_decimal(amount),
            correlation_id,
            json.dumps(metadata or {}),
        )

    return _serialize_row(row)


async def reserve_reward_funding(
    *,
    reward_id: str,
    wallet_id: str,
    tenant_code: str,
    sponsor_code: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = await get_allocation_by_reward(reward_id=reward_id)

    if existing:
        return {
            "reserved": True,
            "already_reserved": True,
            "allocation": existing,
        }

    amount_decimal = _to_decimal(amount)

    wallet_result = await reserve_wallet_funds(
        wallet_id=wallet_id,
        tenant_code=tenant_code,
        amount=amount_decimal,
        correlation_id=correlation_id,
        metadata={
            **(metadata or {}),
            "reward_id": reward_id,
            "sponsor_code": sponsor_code,
            "funding_source": "SPONSOR_WALLET",
        },
    )

    allocation = await create_allocation(
        reward_id=reward_id,
        wallet_id=wallet_id,
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=amount_decimal,
        correlation_id=correlation_id,
        metadata=metadata,
    )

    return {
        "reserved": True,
        "already_reserved": False,
        "wallet": wallet_result,
        "allocation": allocation,
    }


async def release_reward_funding(
    *,
    reward_id: str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    allocation = await get_allocation_by_reward(reward_id=reward_id)

    if not allocation:
        return {"released": False, "reason": "ALLOCATION_NOT_FOUND"}

    if allocation["status"] == "RELEASED":
        return {
            "released": True,
            "already_released": True,
            "allocation": allocation,
        }

    if allocation["status"] != "RESERVED":
        return {
            "released": False,
            "reason": f"INVALID_STATUS_{allocation['status']}",
            "allocation": allocation,
        }

    wallet_result = await release_wallet_reservation(
        wallet_id=allocation["wallet_id"],
        tenant_code=allocation["tenant_code"],
        amount=allocation["amount"],
        correlation_id=correlation_id or allocation.get("correlation_id"),
        metadata={
            **(metadata or {}),
            "reward_id": reward_id,
            "allocation_id": allocation["allocation_id"],
            "funding_source": "SPONSOR_WALLET",
        },
    )

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
        row = await conn.fetchrow(query, allocation["allocation_id"])

    return {
        "released": True,
        "wallet": wallet_result,
        "allocation": _serialize_row(row),
    }


async def debit_reward_funding(
    *,
    reward_id: str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    allocation = await get_allocation_by_reward(reward_id=reward_id)

    if not allocation:
        return {"debited": False, "reason": "ALLOCATION_NOT_FOUND"}

    if allocation["status"] == "DEBITED":
        return {
            "debited": True,
            "already_debited": True,
            "allocation": allocation,
        }

    if allocation["status"] != "RESERVED":
        return {
            "debited": False,
            "reason": f"INVALID_STATUS_{allocation['status']}",
            "allocation": allocation,
        }

    wallet_result = await debit_wallet(
        wallet_id=allocation["wallet_id"],
        tenant_code=allocation["tenant_code"],
        amount=allocation["amount"],
        correlation_id=correlation_id or allocation.get("correlation_id"),
        metadata={
            **(metadata or {}),
            "reward_id": reward_id,
            "allocation_id": allocation["allocation_id"],
            "funding_source": "SPONSOR_WALLET",
        },
    )

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
        row = await conn.fetchrow(query, allocation["allocation_id"])

    return {
        "debited": True,
        "wallet": wallet_result,
        "allocation": _serialize_row(row),
    }


async def reverse_reward_funding(
    *,
    reward_id: str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    allocation = await get_allocation_by_reward(reward_id=reward_id)

    if not allocation:
        return {"reversed": False, "reason": "ALLOCATION_NOT_FOUND"}

    if allocation["status"] == "REVERSED":
        return {
            "reversed": True,
            "already_reversed": True,
            "allocation": allocation,
        }

    if allocation["status"] != "DEBITED":
        return {
            "reversed": False,
            "reason": f"INVALID_STATUS_{allocation['status']}",
            "allocation": allocation,
        }

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
        row = await conn.fetchrow(query, allocation["allocation_id"])

    return {
        "reversed": True,
        "allocation": _serialize_row(row),
    }


async def list_allocations(
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
        rows = await conn.fetch(query, tenant_code, sponsor_code, status, limit)

    return [_serialize_row(row) for row in rows]