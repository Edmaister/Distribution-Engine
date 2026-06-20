from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from services.fulfilment.settlement.lock_enforcement import ensure_period_open
from services.fulfilment.settlement.status import (
    SettlementStatus,
    VALID_SETTLEMENT_STATUSES,
)
from utils.db import db_connection


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _status_value(status: SettlementStatus | str) -> str:
    if isinstance(status, SettlementStatus):
        return status.value

    if status not in VALID_SETTLEMENT_STATUSES:
        raise ValueError(f"Invalid settlement status: {status}")

    return status


def _row_to_dict(row: Any) -> Optional[dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


async def record_pending_settlement(
    *,
    tenant_code: str,
    reward_id: UUID | str,
    audit_id: UUID | str,
    provider_key: str,
    provider_reference: Optional[str],
    amount: Decimal | float | int | str,
    currency: str = "ZAR",
    period_id: UUID | str | None = None,
) -> dict[str, Any]:
    amount_value = _to_decimal(amount)

    if period_id is not None:
        await ensure_period_open(str(period_id))

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO fulfilment_settlement_ledger (
                tenant_code,
                reward_id,
                audit_id,
                provider_key,
                provider_reference,
                amount,
                currency,
                status,
                period_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING
                settlement_id,
                tenant_code,
                reward_id,
                audit_id,
                provider_key,
                provider_reference,
                amount,
                currency,
                status,
                settlement_date,
                settled_at,
                failed_at,
                reversed_at,
                failure_reason,
                reversal_reason,
                created_at,
                updated_at,
                period_id
            """,
            tenant_code,
            str(reward_id),
            str(audit_id),
            provider_key,
            provider_reference,
            amount_value,
            currency,
            SettlementStatus.PENDING.value,
            str(period_id) if period_id is not None else None,
        )

    return dict(row)


async def update_settlement_status(
    *,
    settlement_id: UUID | str,
    status: SettlementStatus | str,
    failure_reason: Optional[str] = None,
    reversal_reason: Optional[str] = None,
) -> dict[str, Any]:
    status_value = _status_value(status)

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE fulfilment_settlement_ledger
            SET
                status = $1,
                settled_at = CASE WHEN $1 = 'SETTLED' THEN NOW() ELSE settled_at END,
                failed_at = CASE WHEN $1 = 'FAILED' THEN NOW() ELSE failed_at END,
                reversed_at = CASE WHEN $1 = 'REVERSED' THEN NOW() ELSE reversed_at END,
                failure_reason = COALESCE($2, failure_reason),
                reversal_reason = COALESCE($3, reversal_reason),
                updated_at = NOW()
            WHERE settlement_id = $4
            RETURNING
                settlement_id,
                tenant_code,
                reward_id,
                audit_id,
                provider_key,
                provider_reference,
                amount,
                currency,
                status,
                settlement_date,
                settled_at,
                failed_at,
                reversed_at,
                failure_reason,
                reversal_reason,
                created_at,
                updated_at,
                period_id
            """,
            status_value,
            failure_reason,
            reversal_reason,
            str(settlement_id),
        )

    if not row:
        raise ValueError(f"Settlement not found: {settlement_id}")

    return dict(row)


async def mark_processing(*, settlement_id: UUID | str) -> dict[str, Any]:
    return await update_settlement_status(
        settlement_id=settlement_id,
        status=SettlementStatus.PROCESSING,
    )


async def mark_settled(*, settlement_id: UUID | str) -> dict[str, Any]:
    return await update_settlement_status(
        settlement_id=settlement_id,
        status=SettlementStatus.SETTLED,
    )


async def mark_failed(
    *,
    settlement_id: UUID | str,
    failure_reason: str,
) -> dict[str, Any]:
    return await update_settlement_status(
        settlement_id=settlement_id,
        status=SettlementStatus.FAILED,
        failure_reason=failure_reason,
    )


async def mark_reversed(
    *,
    settlement_id: UUID | str,
    reversal_reason: str,
) -> dict[str, Any]:
    return await update_settlement_status(
        settlement_id=settlement_id,
        status=SettlementStatus.REVERSED,
        reversal_reason=reversal_reason,
    )


async def mark_disputed(*, settlement_id: UUID | str) -> dict[str, Any]:
    return await update_settlement_status(
        settlement_id=settlement_id,
        status=SettlementStatus.DISPUTED,
    )


async def get_settlement_by_id(
    *,
    settlement_id: UUID | str,
) -> Optional[dict[str, Any]]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                settlement_id,
                tenant_code,
                reward_id,
                audit_id,
                provider_key,
                provider_reference,
                amount,
                currency,
                status,
                settlement_date,
                settled_at,
                failed_at,
                reversed_at,
                failure_reason,
                reversal_reason,
                created_at,
                updated_at,
                period_id
            FROM fulfilment_settlement_ledger
            WHERE settlement_id = $1
            """,
            str(settlement_id),
        )

    return _row_to_dict(row)


async def get_settlement_by_reward(
    *,
    reward_id: UUID | str,
) -> Optional[dict[str, Any]]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                settlement_id,
                tenant_code,
                reward_id,
                audit_id,
                provider_key,
                provider_reference,
                amount,
                currency,
                status,
                settlement_date,
                settled_at,
                failed_at,
                reversed_at,
                failure_reason,
                reversal_reason,
                created_at,
                updated_at,
                period_id
            FROM fulfilment_settlement_ledger
            WHERE reward_id = $1
            ORDER BY created_at DESC
            LIMIT 1
            """,
            str(reward_id),
        )

    return _row_to_dict(row)


async def list_settlements(
    *,
    tenant_code: Optional[str] = None,
    provider_key: Optional[str] = None,
    status: Optional[SettlementStatus | str] = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    filters = []
    params: list[Any] = []

    if tenant_code:
        params.append(tenant_code)
        filters.append(f"tenant_code = ${len(params)}")

    if provider_key:
        params.append(provider_key)
        filters.append(f"provider_key = ${len(params)}")

    if status:
        params.append(_status_value(status))
        filters.append(f"status = ${len(params)}")

    params.append(limit)
    limit_placeholder = f"${len(params)}"

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT
                settlement_id,
                tenant_code,
                reward_id,
                audit_id,
                provider_key,
                provider_reference,
                amount,
                currency,
                status,
                settlement_date,
                settled_at,
                failed_at,
                reversed_at,
                failure_reason,
                reversal_reason,
                created_at,
                updated_at,
                period_id
            FROM fulfilment_settlement_ledger
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit_placeholder}
            """,
            *params,
        )

    return [dict(row) for row in rows]


async def get_provider_exposure(
    *,
    tenant_code: Optional[str] = None,
    provider_key: Optional[str] = None,
) -> list[dict[str, Any]]:
    filters = ["status IN ('PENDING', 'PROCESSING', 'FAILED', 'DISPUTED')"]
    params: list[Any] = []

    if tenant_code:
        params.append(tenant_code)
        filters.append(f"tenant_code = ${len(params)}")

    if provider_key:
        params.append(provider_key)
        filters.append(f"provider_key = ${len(params)}")

    where_clause = "WHERE " + " AND ".join(filters)

    async with db_connection() as conn:
        rows = await conn.fetch(
            f"""
            SELECT
                tenant_code,
                provider_key,
                currency,
                COUNT(*) AS settlement_count,
                COALESCE(SUM(amount), 0) AS exposure_amount
            FROM fulfilment_settlement_ledger
            {where_clause}
            GROUP BY tenant_code, provider_key, currency
            ORDER BY exposure_amount DESC
            """,
            *params,
        )

    return [dict(row) for row in rows]