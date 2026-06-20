from __future__ import annotations

from decimal import Decimal
from typing import Any

from services.marketplace_funding.sponsor_wallet_ledger_repository import (
    create_ledger_entry,
    list_wallet_ledger,
)


async def record_wallet_transaction(
    *,
    wallet_id: str,
    tenant_code: str,
    transaction_type: str,
    amount: Decimal | int | float | str,
    balance_before: Decimal | int | float | str,
    balance_after: Decimal | int | float | str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return await create_ledger_entry(
        wallet_id=wallet_id,
        tenant_code=tenant_code,
        transaction_type=transaction_type,
        amount=Decimal(str(amount)),
        balance_before=Decimal(str(balance_before)),
        balance_after=Decimal(str(balance_after)),
        correlation_id=correlation_id,
        metadata=metadata or {},
    )


async def list_sponsor_wallet_transactions(
    *,
    wallet_id: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return await list_wallet_ledger(
        wallet_id=wallet_id,
        limit=limit,
    )