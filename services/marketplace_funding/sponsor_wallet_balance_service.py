# services/marketplace_funding/sponsor_wallet_balance_service.py

from __future__ import annotations

from decimal import Decimal
from typing import Any

from services.marketplace_funding.sponsor_wallet_repository import (
    update_wallet_balances,
)
from services.marketplace_funding.sponsor_wallet_ledger_service import (
    record_wallet_transaction,
)
from services.marketplace_funding.sponsor_wallet_service import (
    enrich_wallet_balance,
    get_sponsor_wallet,
)


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))


def _ensure_positive(amount: Decimal) -> None:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")


def _ensure_wallet_tenant(
    *,
    wallet: dict[str, Any],
    tenant_code: str,
) -> None:
    if wallet["tenant_code"] != tenant_code:
        raise ValueError("Sponsor wallet does not belong to tenant")


async def topup_wallet(
    *,
    wallet_id: str,
    tenant_code: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_sponsor_wallet(wallet_id=wallet_id)
    if not wallet:
        raise ValueError("Sponsor wallet not found")

    _ensure_wallet_tenant(wallet=wallet, tenant_code=tenant_code)

    current_balance = _to_decimal(wallet["current_balance"])
    reserved_balance = _to_decimal(wallet["reserved_balance"])

    new_current_balance = current_balance + amount_decimal

    updated_wallet = await update_wallet_balances(
        wallet_id=wallet_id,
        current_balance=new_current_balance,
        reserved_balance=reserved_balance,
    )

    if not updated_wallet:
        raise ValueError("Sponsor wallet update failed")

    await record_wallet_transaction(
        wallet_id=wallet_id,
        tenant_code=tenant_code,
        transaction_type="TOPUP",
        amount=amount_decimal,
        balance_before=current_balance,
        balance_after=new_current_balance,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )

    return enrich_wallet_balance(updated_wallet)


async def reserve_wallet_funds(
    *,
    wallet_id: str,
    tenant_code: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_sponsor_wallet(wallet_id=wallet_id)
    if not wallet:
        raise ValueError("Sponsor wallet not found")

    _ensure_wallet_tenant(wallet=wallet, tenant_code=tenant_code)

    current_balance = _to_decimal(wallet["current_balance"])
    reserved_balance = _to_decimal(wallet["reserved_balance"])
    available_balance = current_balance - reserved_balance

    if amount_decimal > available_balance:
        raise ValueError("Insufficient available wallet balance")

    new_reserved_balance = reserved_balance + amount_decimal

    updated_wallet = await update_wallet_balances(
        wallet_id=wallet_id,
        current_balance=current_balance,
        reserved_balance=new_reserved_balance,
    )

    if not updated_wallet:
        raise ValueError("Sponsor wallet update failed")

    await record_wallet_transaction(
        wallet_id=wallet_id,
        tenant_code=tenant_code,
        transaction_type="RESERVE",
        amount=amount_decimal,
        balance_before=reserved_balance,
        balance_after=new_reserved_balance,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )

    return enrich_wallet_balance(updated_wallet)


async def release_wallet_reservation(
    *,
    wallet_id: str,
    tenant_code: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_sponsor_wallet(wallet_id=wallet_id)
    if not wallet:
        raise ValueError("Sponsor wallet not found")

    _ensure_wallet_tenant(wallet=wallet, tenant_code=tenant_code)

    current_balance = _to_decimal(wallet["current_balance"])
    reserved_balance = _to_decimal(wallet["reserved_balance"])

    if amount_decimal > reserved_balance:
        raise ValueError("Cannot release more than reserved balance")

    new_reserved_balance = reserved_balance - amount_decimal

    updated_wallet = await update_wallet_balances(
        wallet_id=wallet_id,
        current_balance=current_balance,
        reserved_balance=new_reserved_balance,
    )

    if not updated_wallet:
        raise ValueError("Sponsor wallet update failed")

    await record_wallet_transaction(
        wallet_id=wallet_id,
        tenant_code=tenant_code,
        transaction_type="RELEASE",
        amount=amount_decimal,
        balance_before=reserved_balance,
        balance_after=new_reserved_balance,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )

    return enrich_wallet_balance(updated_wallet)


async def debit_wallet(
    *,
    wallet_id: str,
    tenant_code: str,
    amount: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    amount_decimal = _to_decimal(amount)
    _ensure_positive(amount_decimal)

    wallet = await get_sponsor_wallet(wallet_id=wallet_id)
    if not wallet:
        raise ValueError("Sponsor wallet not found")

    _ensure_wallet_tenant(wallet=wallet, tenant_code=tenant_code)

    current_balance = _to_decimal(wallet["current_balance"])
    reserved_balance = _to_decimal(wallet["reserved_balance"])

    if amount_decimal > current_balance:
        raise ValueError("Insufficient current wallet balance")

    if amount_decimal > reserved_balance:
        raise ValueError("Cannot debit more than reserved balance")

    new_current_balance = current_balance - amount_decimal
    new_reserved_balance = reserved_balance - amount_decimal

    updated_wallet = await update_wallet_balances(
        wallet_id=wallet_id,
        current_balance=new_current_balance,
        reserved_balance=new_reserved_balance,
    )

    if not updated_wallet:
        raise ValueError("Sponsor wallet update failed")

    await record_wallet_transaction(
        wallet_id=wallet_id,
        tenant_code=tenant_code,
        transaction_type="DEBIT",
        amount=amount_decimal,
        balance_before=current_balance,
        balance_after=new_current_balance,
        correlation_id=correlation_id,
        metadata=metadata or {},
    )

    return enrich_wallet_balance(updated_wallet)