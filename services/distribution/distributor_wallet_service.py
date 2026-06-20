from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from utils.db import db_connection


WALLET_STATUS_ACTIVE = "ACTIVE"


class DistributorWalletError(Exception):
    pass


class DistributorWalletNotFound(DistributorWalletError):
    pass


class DistributorWalletDistributorNotFound(DistributorWalletError):
    pass


class DistributorWalletInsufficientBalance(DistributorWalletError):
    pass


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


def _ensure_positive(amount: Decimal) -> None:
    if amount <= 0:
        raise DistributorWalletError("Amount must be greater than zero")


def _json(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {})


def _serialize(row: Any) -> dict[str, Any]:
    result = {
        key: str(value) if isinstance(value, UUID) else value
        for key, value in dict(row).items()
    }

    if isinstance(result.get("metadata"), str):
        result["metadata"] = json.loads(result["metadata"])

    return result


async def create_distributor_wallet(
    *,
    distributor_id: str,
    currency: str = "ZAR",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        distributor = await conn.fetchrow(
            """
            SELECT distributor_id, tenant_code, distributor_code
            FROM distribution_distributors
            WHERE distributor_id = $1
            """,
            distributor_id,
        )

        if not distributor:
            raise DistributorWalletDistributorNotFound("Distributor not found")

        row = await conn.fetchrow(
            """
            INSERT INTO distribution_distributor_wallets (
                wallet_id,
                distributor_id,
                tenant_code,
                distributor_code,
                currency,
                status,
                metadata
            )
            VALUES ($1, $2, $3, $4, $5, 'ACTIVE', $6::jsonb)
            ON CONFLICT (distributor_id, currency)
            DO UPDATE SET
                metadata = distribution_distributor_wallets.metadata || EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING *
            """,
            uuid4(),
            distributor["distributor_id"],
            distributor["tenant_code"],
            distributor["distributor_code"],
            currency,
            _json(metadata),
        )

    return _serialize(row)


async def get_distributor_wallet(
    *,
    wallet_id: str,
) -> dict[str, Any]:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM distribution_distributor_wallets
            WHERE wallet_id = $1
            """,
            wallet_id,
        )

    if not row:
        raise DistributorWalletNotFound("Distributor wallet not found")

    return _serialize(row)


async def list_distributor_wallets(
    *,
    tenant_code: str,
    distributor_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_distributor_wallets
            WHERE tenant_code = $1
              AND ($2::uuid IS NULL OR distributor_id = $2)
              AND ($3::text IS NULL OR status = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            tenant_code,
            distributor_id,
            status,
            limit,
        )

    return [_serialize(row) for row in rows]


async def credit_distributor_wallet(
    *,
    wallet_id: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    return await _apply_wallet_movement(
        wallet_id=wallet_id,
        transaction_type="CREDIT",
        amount=amount_decimal,
        current_delta=amount_decimal,
        available_delta=amount_decimal,
        balance_key="current_balance",
        correlation_id=correlation_id,
        metadata=metadata,
    )


async def hold_distributor_wallet_funds(
    *,
    wallet_id: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_distributor_wallet(wallet_id=wallet_id)
    if amount_decimal > _to_decimal(wallet["available_balance"]):
        raise DistributorWalletInsufficientBalance("Insufficient available wallet balance")

    return await _apply_wallet_movement(
        wallet_id=wallet_id,
        transaction_type="HOLD",
        amount=amount_decimal,
        available_delta=-amount_decimal,
        held_delta=amount_decimal,
        balance_key="held_balance",
        correlation_id=correlation_id,
        metadata=metadata,
    )


async def release_distributor_wallet_hold(
    *,
    wallet_id: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_distributor_wallet(wallet_id=wallet_id)
    if amount_decimal > _to_decimal(wallet["held_balance"]):
        raise DistributorWalletInsufficientBalance("Cannot release more than held balance")

    return await _apply_wallet_movement(
        wallet_id=wallet_id,
        transaction_type="RELEASE_HOLD",
        amount=amount_decimal,
        available_delta=amount_decimal,
        held_delta=-amount_decimal,
        balance_key="held_balance",
        correlation_id=correlation_id,
        metadata=metadata,
    )


async def payout_distributor_wallet(
    *,
    wallet_id: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_distributor_wallet(wallet_id=wallet_id)
    if amount_decimal > _to_decimal(wallet["held_balance"]):
        raise DistributorWalletInsufficientBalance("Cannot pay out more than held balance")

    return await _apply_wallet_movement(
        wallet_id=wallet_id,
        transaction_type="PAYOUT",
        amount=amount_decimal,
        current_delta=-amount_decimal,
        held_delta=-amount_decimal,
        paid_out_delta=amount_decimal,
        balance_key="current_balance",
        correlation_id=correlation_id,
        metadata=metadata,
    )


async def reverse_distributor_wallet_earning(
    *,
    wallet_id: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_distributor_wallet(wallet_id=wallet_id)
    if amount_decimal > _to_decimal(wallet["available_balance"]):
        raise DistributorWalletInsufficientBalance("Cannot reverse more than available balance")

    return await _apply_wallet_movement(
        wallet_id=wallet_id,
        transaction_type="REVERSAL",
        amount=amount_decimal,
        current_delta=-amount_decimal,
        available_delta=-amount_decimal,
        reversed_delta=amount_decimal,
        balance_key="current_balance",
        correlation_id=correlation_id,
        metadata=metadata,
    )


async def list_distributor_wallet_ledger(
    *,
    wallet_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM distribution_distributor_wallet_ledger
            WHERE wallet_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            wallet_id,
            limit,
        )

    return [_serialize(row) for row in rows]


async def _apply_wallet_movement(
    *,
    wallet_id: str,
    transaction_type: str,
    amount: Decimal,
    balance_key: str,
    current_delta: Decimal = Decimal("0"),
    available_delta: Decimal = Decimal("0"),
    held_delta: Decimal = Decimal("0"),
    paid_out_delta: Decimal = Decimal("0"),
    reversed_delta: Decimal = Decimal("0"),
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    async with db_connection() as conn:
        async with conn.transaction():
            wallet = await conn.fetchrow(
                """
                SELECT *
                FROM distribution_distributor_wallets
                WHERE wallet_id = $1
                FOR UPDATE
                """,
                wallet_id,
            )

            if not wallet:
                raise DistributorWalletNotFound("Distributor wallet not found")

            balance_before = _to_decimal(wallet[balance_key])

            updated = await conn.fetchrow(
                """
                UPDATE distribution_distributor_wallets
                SET
                    current_balance = current_balance + $2,
                    available_balance = available_balance + $3,
                    held_balance = held_balance + $4,
                    paid_out_balance = paid_out_balance + $5,
                    reversed_balance = reversed_balance + $6,
                    updated_at = NOW()
                WHERE wallet_id = $1
                RETURNING *
                """,
                wallet_id,
                current_delta,
                available_delta,
                held_delta,
                paid_out_delta,
                reversed_delta,
            )

            balance_after = _to_decimal(updated[balance_key])

            await conn.fetchrow(
                """
                INSERT INTO distribution_distributor_wallet_ledger (
                    ledger_id,
                    wallet_id,
                    distributor_id,
                    tenant_code,
                    transaction_type,
                    amount,
                    balance_before,
                    balance_after,
                    correlation_id,
                    metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb)
                RETURNING *
                """,
                uuid4(),
                wallet_id,
                wallet["distributor_id"],
                wallet["tenant_code"],
                transaction_type,
                amount,
                balance_before,
                balance_after,
                correlation_id,
                _json(metadata),
            )

    return _serialize(updated)
