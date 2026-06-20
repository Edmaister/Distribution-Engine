# services/marketplace_funding/sponsor_wallet_service.py

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from services.marketplace_funding.sponsor_wallet_repository import (
    create_wallet,
    get_wallet,
    list_wallets,
    get_wallet_by_sponsor,
)


def enrich_wallet_balance(
    wallet: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in wallet.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        else:
            result[key] = value

    current_balance = Decimal(str(result["current_balance"]))
    reserved_balance = Decimal(str(result["reserved_balance"]))

    result["available_balance"] = current_balance - reserved_balance

    return result


async def create_sponsor_wallet(
    *,
    tenant_code: str,
    sponsor_code: str,
    sponsor_name: str,
    currency: str = "ZAR",
) -> dict[str, Any]:
    wallet = await create_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        sponsor_name=sponsor_name,
        currency=currency,
    )

    return enrich_wallet_balance(wallet)


async def get_sponsor_wallet(
    *,
    wallet_id: str,
) -> dict[str, Any] | None:
    wallet = await get_wallet(wallet_id=wallet_id)

    if not wallet:
        return None

    return enrich_wallet_balance(wallet)

async def list_sponsor_wallets(
    *,
    tenant_code: str,
    sponsor_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    wallets = await list_wallets(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        status=status,
        limit=limit,
    )

    return [enrich_wallet_balance(wallet) for wallet in wallets]

async def get_sponsor_wallet_by_sponsor(
    *,
    tenant_code: str,
    sponsor_code: str,
) -> dict[str, Any] | None:
    wallet = await get_wallet_by_sponsor(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    if not wallet:
        return None

    return enrich_wallet_balance(wallet)