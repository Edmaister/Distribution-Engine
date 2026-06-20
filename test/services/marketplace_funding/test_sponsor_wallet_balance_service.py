from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.marketplace_funding.sponsor_wallet_balance_service import (
    debit_wallet,
    release_wallet_reservation,
    reserve_wallet_funds,
    topup_wallet,
)
from services.marketplace_funding.sponsor_wallet_service import (
    create_sponsor_wallet,
    get_sponsor_wallet,
)

pytestmark = pytest.mark.asyncio


def unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}".upper()


async def create_test_wallet():
    return await create_sponsor_wallet(
        tenant_code="FNB",
        sponsor_code=unique_code("WALLET"),
        sponsor_name="Wallet Test",
        currency="ZAR",
    )


async def test_topup_wallet():
    wallet = await create_test_wallet()

    updated = await topup_wallet(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount=Decimal("1000.00"),
    )

    assert updated["current_balance"] == Decimal("1000.00")
    assert updated["reserved_balance"] == Decimal("0.00")
    assert updated["available_balance"] == Decimal("1000.00")


async def test_topup_wallet_requires_positive_amount():
    wallet = await create_test_wallet()

    with pytest.raises(ValueError):
        await topup_wallet(
            tenant_code=wallet["tenant_code"],
            wallet_id=str(wallet["wallet_id"]),
            amount=Decimal("0.00"),
        )


async def test_reserve_wallet_funds():
    wallet = await create_test_wallet()

    await topup_wallet(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="1000.00",
    )

    updated = await reserve_wallet_funds(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="250.00",
    )

    assert updated["current_balance"] == Decimal("1000.00")
    assert updated["reserved_balance"] == Decimal("250.00")
    assert updated["available_balance"] == Decimal("750.00")


async def test_reserve_wallet_funds_insufficient_balance():
    wallet = await create_test_wallet()

    with pytest.raises(ValueError):
        await reserve_wallet_funds(
            tenant_code=wallet["tenant_code"],
            wallet_id=str(wallet["wallet_id"]),
            amount="100.00",
        )


async def test_release_wallet_reservation():
    wallet = await create_test_wallet()

    await topup_wallet(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="1000.00",
    )

    await reserve_wallet_funds(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="300.00",
    )

    updated = await release_wallet_reservation(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="100.00",
    )

    assert updated["reserved_balance"] == Decimal("200.00")
    assert updated["available_balance"] == Decimal("800.00")


async def test_release_wallet_reservation_cannot_exceed_reserved():
    wallet = await create_test_wallet()

    with pytest.raises(ValueError):
        await release_wallet_reservation(
            tenant_code=wallet["tenant_code"],
            wallet_id=str(wallet["wallet_id"]),
            amount="100.00",
        )


async def test_debit_wallet():
    wallet = await create_test_wallet()

    await topup_wallet(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="1000.00",
    )

    await reserve_wallet_funds(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="300.00",
    )

    updated = await debit_wallet(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="300.00",
    )

    assert updated["current_balance"] == Decimal("700.00")
    assert updated["reserved_balance"] == Decimal("0.00")
    assert updated["available_balance"] == Decimal("700.00")


async def test_debit_wallet_requires_reserved_balance():
    wallet = await create_test_wallet()

    await topup_wallet(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="1000.00",
    )

    with pytest.raises(ValueError):
        await debit_wallet(
            tenant_code=wallet["tenant_code"],
            wallet_id=str(wallet["wallet_id"]),
            amount="100.00",
        )


async def test_wallet_state_after_multiple_operations():
    wallet = await create_test_wallet()

    await topup_wallet(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="2000.00",
    )

    await reserve_wallet_funds(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="500.00",
    )

    await release_wallet_reservation(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="100.00",
    )

    await reserve_wallet_funds(
        tenant_code=wallet["tenant_code"],
        wallet_id=str(wallet["wallet_id"]),
        amount="200.00",
    )

    current = await get_sponsor_wallet(
        wallet_id=str(wallet["wallet_id"]),
    )

    assert current["current_balance"] == Decimal("2000.00")
    assert current["reserved_balance"] == Decimal("600.00")
    assert current["available_balance"] == Decimal("1400.00")