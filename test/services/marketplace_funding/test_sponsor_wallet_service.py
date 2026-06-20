from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.marketplace_funding.sponsor_wallet_service import (
    create_sponsor_wallet,
    enrich_wallet_balance,
    get_sponsor_wallet,
    get_sponsor_wallet_by_sponsor,
    list_sponsor_wallets,
)


pytestmark = pytest.mark.asyncio


def unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}".upper()


async def test_enrich_wallet_balance_calculates_available_balance():
    wallet = {
        "current_balance": Decimal("1000.00"),
        "reserved_balance": Decimal("250.00"),
    }

    result = enrich_wallet_balance(wallet)

    assert result["available_balance"] == Decimal("750.00")


async def test_create_sponsor_wallet():
    sponsor_code = unique_code("MTN")

    wallet = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="MTN SA",
        currency="ZAR",
    )

    assert wallet["tenant_code"] == "FNB"
    assert wallet["sponsor_code"] == sponsor_code
    assert wallet["sponsor_name"] == "MTN SA"
    assert wallet["currency"] == "ZAR"
    assert wallet["current_balance"] == Decimal("0.00")
    assert wallet["reserved_balance"] == Decimal("0.00")
    assert wallet["available_balance"] == Decimal("0.00")
    assert wallet["status"] == "ACTIVE"


async def test_create_sponsor_wallet_is_idempotent_on_sponsor_currency():
    sponsor_code = unique_code("DISCOVERY")

    first = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Discovery",
        currency="ZAR",
    )

    second = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Discovery Health",
        currency="ZAR",
    )

    assert second["wallet_id"] == first["wallet_id"]
    assert second["sponsor_name"] == "Discovery Health"


async def test_get_sponsor_wallet():
    created = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=unique_code("PNP"),
        sponsor_name="Pick n Pay",
        currency="ZAR",
    )

    wallet = await get_sponsor_wallet(wallet_id=str(created["wallet_id"]))

    assert wallet is not None
    assert wallet["wallet_id"] == created["wallet_id"]
    assert wallet["available_balance"] == Decimal("0.00")


async def test_get_sponsor_wallet_returns_none_when_missing():
    wallet = await get_sponsor_wallet(wallet_id=str(uuid4()))

    assert wallet is None


async def test_get_sponsor_wallet_by_sponsor():
    sponsor_code = unique_code("BOXER")

    created = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Boxer",
        currency="ZAR",
    )

    wallet = await get_sponsor_wallet_by_sponsor(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
    )

    assert wallet is not None
    assert wallet["wallet_id"] == created["wallet_id"]
    assert wallet["currency"] == "ZAR"


async def test_get_sponsor_wallet_by_sponsor_returns_none_when_missing():
    wallet = await get_sponsor_wallet_by_sponsor(
        tenant_code="FNB",
        sponsor_code=unique_code("MISSING"),
    )

    assert wallet is None


async def test_list_sponsor_wallets():
    sponsor_code = unique_code("MOMENTUM")

    created = await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=sponsor_code,
        sponsor_name="Momentum",
        currency="ZAR",
    )

    wallets = await list_sponsor_wallets(
        tenant_code="FNB",
        limit=100,
    )

    wallet_ids = {wallet["wallet_id"] for wallet in wallets}

    assert created["wallet_id"] in wallet_ids
    assert all("available_balance" in wallet for wallet in wallets)