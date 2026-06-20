from __future__ import annotations
import json

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from utils.db import db_connection


class FundingError(Exception):
    """Base funding engine error."""


class FundingAccountNotFound(FundingError):
    """Raised when a funding account cannot be found."""


class InsufficientAvailableBalance(FundingError):
    """Raised when available balance is insufficient."""


class InvalidFundingAmount(FundingError):
    """Raised when amount is invalid."""

def _metadata_json(metadata: dict[str, Any] | None) -> str:
    return json.dumps(metadata or {})

def _to_decimal(amount: Decimal | int | float | str) -> Decimal:
    value = Decimal(str(amount))

    if value <= 0:
        raise InvalidFundingAmount("Amount must be greater than zero")

    return value.quantize(Decimal("0.01"))


async def create_funding_account(
    *,
    tenant_code: str,
    account_name: str,
    account_type: str,
    currency_code: str = "ZAR",
    opening_balance: Decimal | int | float | str = Decimal("0.00"),
    status: str = "ACTIVE",
) -> dict[str, Any]:
    account_id = uuid4()
    balance = Decimal(str(opening_balance)).quantize(Decimal("0.01"))

    if balance < 0:
        raise InvalidFundingAmount("Opening balance cannot be negative")

    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO funding_accounts (
                account_id,
                tenant_code,
                account_name,
                account_type,
                currency_code,
                current_balance,
                reserved_balance,
                available_balance,
                status
            )
            VALUES ($1, $2, $3, $4, $5, $6, 0, $6, $7)
            RETURNING *
            """,
            account_id,
            tenant_code,
            account_name,
            account_type,
            currency_code,
            balance,
            status,
        )

    return dict(row)


async def get_funding_account(
    *,
    account_id: UUID | str,
) -> dict[str, Any] | None:
    async with db_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM funding_accounts
            WHERE account_id = $1
            """,
            UUID(str(account_id)),
        )

    return dict(row) if row else None


async def list_funding_accounts(
    *,
    tenant_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_accounts
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


async def credit_account(
    *,
    account_id: UUID | str,
    amount: Decimal | int | float | str,
    reference_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)
    tx_id = uuid4()

    async with db_connection() as conn:
        async with conn.transaction():
            account = await conn.fetchrow(
                """
                SELECT *
                FROM funding_accounts
                WHERE account_id = $1
                FOR UPDATE
                """,
                UUID(str(account_id)),
            )

            if not account:
                raise FundingAccountNotFound("Funding account not found")

            updated = await conn.fetchrow(
                """
                UPDATE funding_accounts
                SET current_balance = current_balance + $2,
                    available_balance = available_balance + $2,
                    updated_at = NOW()
                WHERE account_id = $1
                RETURNING *
                """,
                UUID(str(account_id)),
                value,
            )

            tx = await conn.fetchrow(
                """
                INSERT INTO funding_transactions (
                    transaction_id,
                    account_id,
                    tenant_code,
                    transaction_type,
                    amount,
                    reference_id,
                    correlation_id,
                    metadata
                )
                VALUES ($1, $2, $3, 'CREDIT', $4, $5, $6, $7)
                RETURNING *
                """,
                tx_id,
                UUID(str(account_id)),
                account["tenant_code"],
                value,
                reference_id,
                correlation_id,
                _metadata_json(metadata),
            )

    return {
        "account": dict(updated),
        "transaction": dict(tx),
    }


async def debit_account(
    *,
    account_id: UUID | str,
    amount: Decimal | int | float | str,
    reference_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)
    tx_id = uuid4()

    async with db_connection() as conn:
        async with conn.transaction():
            account = await conn.fetchrow(
                """
                SELECT *
                FROM funding_accounts
                WHERE account_id = $1
                FOR UPDATE
                """,
                UUID(str(account_id)),
            )

            if not account:
                raise FundingAccountNotFound("Funding account not found")

            if account["available_balance"] < value:
                raise InsufficientAvailableBalance("Insufficient available balance")

            updated = await conn.fetchrow(
                """
                UPDATE funding_accounts
                SET current_balance = current_balance - $2,
                    available_balance = available_balance - $2,
                    updated_at = NOW()
                WHERE account_id = $1
                RETURNING *
                """,
                UUID(str(account_id)),
                value,
            )

            tx = await conn.fetchrow(
                """
                INSERT INTO funding_transactions (
                    transaction_id,
                    account_id,
                    tenant_code,
                    transaction_type,
                    amount,
                    reference_id,
                    correlation_id,
                    metadata
                )
                VALUES ($1, $2, $3, 'DEBIT', $4, $5, $6, $7)
                RETURNING *
                """,
                tx_id,
                UUID(str(account_id)),
                account["tenant_code"],
                value,
                reference_id,
                correlation_id,
                _metadata_json(metadata),
            )

    return {
        "account": dict(updated),
        "transaction": dict(tx),
    }


async def reserve_funds(
    *,
    account_id: UUID | str,
    amount: Decimal | int | float | str,
    reference_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)
    tx_id = uuid4()

    async with db_connection() as conn:
        async with conn.transaction():
            account = await conn.fetchrow(
                """
                SELECT *
                FROM funding_accounts
                WHERE account_id = $1
                FOR UPDATE
                """,
                UUID(str(account_id)),
            )

            if not account:
                raise FundingAccountNotFound("Funding account not found")

            if account["available_balance"] < value:
                raise InsufficientAvailableBalance("Insufficient available balance")

            updated = await conn.fetchrow(
                """
                UPDATE funding_accounts
                SET reserved_balance = reserved_balance + $2,
                    available_balance = available_balance - $2,
                    updated_at = NOW()
                WHERE account_id = $1
                RETURNING *
                """,
                UUID(str(account_id)),
                value,
            )

            tx = await conn.fetchrow(
                """
                INSERT INTO funding_transactions (
                    transaction_id,
                    account_id,
                    tenant_code,
                    transaction_type,
                    amount,
                    reference_id,
                    correlation_id,
                    metadata
                )
                VALUES ($1, $2, $3, 'RESERVE', $4, $5, $6, $7)
                RETURNING *
                """,
                tx_id,
                UUID(str(account_id)),
                account["tenant_code"],
                value,
                reference_id,
                correlation_id,
                _metadata_json(metadata),
            )

    return {
        "account": dict(updated),
        "transaction": dict(tx),
    }


async def release_reserved_funds(
    *,
    account_id: UUID | str,
    amount: Decimal | int | float | str,
    reference_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)
    tx_id = uuid4()

    async with db_connection() as conn:
        async with conn.transaction():
            account = await conn.fetchrow(
                """
                SELECT *
                FROM funding_accounts
                WHERE account_id = $1
                FOR UPDATE
                """,
                UUID(str(account_id)),
            )

            if not account:
                raise FundingAccountNotFound("Funding account not found")

            if account["reserved_balance"] < value:
                raise InsufficientAvailableBalance("Insufficient reserved balance")

            updated = await conn.fetchrow(
                """
                UPDATE funding_accounts
                SET reserved_balance = reserved_balance - $2,
                    available_balance = available_balance + $2,
                    updated_at = NOW()
                WHERE account_id = $1
                RETURNING *
                """,
                UUID(str(account_id)),
                value,
            )

            tx = await conn.fetchrow(
                """
                INSERT INTO funding_transactions (
                    transaction_id,
                    account_id,
                    tenant_code,
                    transaction_type,
                    amount,
                    reference_id,
                    correlation_id,
                    metadata
                )
                VALUES ($1, $2, $3, 'RELEASE', $4, $5, $6, $7)
                RETURNING *
                """,
                tx_id,
                UUID(str(account_id)),
                account["tenant_code"],
                value,
                reference_id,
                correlation_id,
                _metadata_json(metadata),
            )

    return {
        "account": dict(updated),
        "transaction": dict(tx),
    }


async def settle_reserved_funds(
    *,
    account_id: UUID | str,
    amount: Decimal | int | float | str,
    reference_id: str | None = None,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = _to_decimal(amount)
    tx_id = uuid4()

    async with db_connection() as conn:
        async with conn.transaction():
            account = await conn.fetchrow(
                """
                SELECT *
                FROM funding_accounts
                WHERE account_id = $1
                FOR UPDATE
                """,
                UUID(str(account_id)),
            )

            if not account:
                raise FundingAccountNotFound("Funding account not found")

            if account["reserved_balance"] < value:
                raise InsufficientAvailableBalance("Insufficient reserved balance")

            updated = await conn.fetchrow(
                """
                UPDATE funding_accounts
                SET current_balance = current_balance - $2,
                    reserved_balance = reserved_balance - $2,
                    updated_at = NOW()
                WHERE account_id = $1
                RETURNING *
                """,
                UUID(str(account_id)),
                value,
            )

            tx = await conn.fetchrow(
                """
                INSERT INTO funding_transactions (
                    transaction_id,
                    account_id,
                    tenant_code,
                    transaction_type,
                    amount,
                    reference_id,
                    correlation_id,
                    metadata
                )
                VALUES ($1, $2, $3, 'SETTLEMENT', $4, $5, $6, $7)
                RETURNING *
                """,
                tx_id,
                UUID(str(account_id)),
                account["tenant_code"],
                value,
                reference_id,
                correlation_id,
                _metadata_json(metadata),
            )

    return {
        "account": dict(updated),
        "transaction": dict(tx),
    }


async def get_account_balance(
    *,
    account_id: UUID | str,
) -> dict[str, Any]:
    account = await get_funding_account(account_id=account_id)

    if not account:
        raise FundingAccountNotFound("Funding account not found")

    return {
        "account_id": account["account_id"],
        "tenant_code": account["tenant_code"],
        "currency_code": account["currency_code"],
        "current_balance": account["current_balance"],
        "reserved_balance": account["reserved_balance"],
        "available_balance": account["available_balance"],
        "status": account["status"],
    }


async def list_funding_transactions(
    *,
    account_id: UUID | str | None = None,
    tenant_code: str | None = None,
    transaction_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT *
            FROM funding_transactions
            WHERE ($1::uuid IS NULL OR account_id = $1)
              AND ($2::text IS NULL OR tenant_code = $2)
              AND ($3::text IS NULL OR transaction_type = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            UUID(str(account_id)) if account_id else None,
            tenant_code,
            transaction_type,
            limit,
        )

    return [dict(row) for row in rows]