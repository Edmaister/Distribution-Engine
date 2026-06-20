from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.reservations import (
    FundingReservationNotFound,
    create_funding_reservation,
    get_funding_reservation,
    get_funding_reservation_by_reward,
    list_funding_reservations,
    mark_reservation_released,
    mark_reservation_settled,
)
from services.funding_service import create_funding_account, reserve_funds


pytestmark = pytest.mark.asyncio


def unique_reward_id(prefix: str = "REWARD") -> str:
    return f"{prefix}-{uuid4()}"


def unique_tenant_code(prefix: str = "TENANT") -> str:
    return f"{prefix}_{uuid4().hex[:8].upper()}"


async def _create_reserved_funding_transaction(
    *,
    tenant_code: str | None = None,
    reward_id: str | None = None,
    amount: str = "100.00",
) -> tuple[dict, dict, str, str]:
    tenant = tenant_code or unique_tenant_code("FNB")
    reward = reward_id or unique_reward_id("REWARD-RES")

    account = await create_funding_account(
        tenant_code=tenant,
        account_name=f"{tenant} Reservation Test Wallet",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )

    funding_result = await reserve_funds(
        account_id=account["account_id"],
        amount=amount,
        reference_id=reward,
        correlation_id=f"CORR-{reward}",
    )

    return account, funding_result["transaction"], tenant, reward


async def test_create_and_get_funding_reservation_by_id():
    account, transaction, tenant_code, reward_id = (
        await _create_reserved_funding_transaction()
    )

    reservation = await create_funding_reservation(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=account["account_id"],
        amount=Decimal("100.00"),
        funding_transaction_id=transaction["transaction_id"],
        correlation_id=f"CORR-{uuid4()}",
    )

    found = await get_funding_reservation(
        reservation_id=reservation["reservation_id"],
    )

    assert found is not None
    assert found["reservation_id"] == reservation["reservation_id"]
    assert found["reward_id"] == reward_id
    assert found["status"] == "RESERVED"


async def test_get_missing_funding_reservation_returns_none():
    found = await get_funding_reservation(
        reservation_id="00000000-0000-0000-0000-000000000000",
    )

    assert found is None


async def test_get_missing_funding_reservation_by_reward_returns_none():
    found = await get_funding_reservation_by_reward(
        reward_id=unique_reward_id("MISSING"),
    )

    assert found is None


async def test_mark_reservation_released():
    account, transaction, tenant_code, reward_id = (
        await _create_reserved_funding_transaction()
    )

    await create_funding_reservation(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=account["account_id"],
        amount=Decimal("100.00"),
        funding_transaction_id=transaction["transaction_id"],
    )

    released = await mark_reservation_released(
        reward_id=reward_id,
    )

    assert released["reward_id"] == reward_id
    assert released["status"] == "RELEASED"


async def test_mark_reservation_released_missing_raises():
    with pytest.raises(FundingReservationNotFound):
        await mark_reservation_released(
            reward_id=unique_reward_id("MISSING-REL"),
        )


async def test_mark_reservation_settled():
    account, transaction, tenant_code, reward_id = (
        await _create_reserved_funding_transaction()
    )

    await create_funding_reservation(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=account["account_id"],
        amount=Decimal("100.00"),
        funding_transaction_id=transaction["transaction_id"],
    )

    settled = await mark_reservation_settled(
        reward_id=reward_id,
    )

    assert settled["reward_id"] == reward_id
    assert settled["status"] == "SETTLED"


async def test_mark_reservation_settled_missing_raises():
    with pytest.raises(FundingReservationNotFound):
        await mark_reservation_settled(
            reward_id=unique_reward_id("MISSING-SET"),
        )


async def test_list_funding_reservations_by_tenant_and_status():
    tenant_code = unique_tenant_code("LIST_TENANT")
    reward_id = unique_reward_id("REWARD-LIST")

    account, transaction, _, _ = await _create_reserved_funding_transaction(
        tenant_code=tenant_code,
        reward_id=reward_id,
        amount="125.00",
    )

    await create_funding_reservation(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=account["account_id"],
        amount=Decimal("125.00"),
        funding_transaction_id=transaction["transaction_id"],
        correlation_id=f"CORR-{uuid4()}",
    )

    reservations = await list_funding_reservations(
        tenant_code=tenant_code,
        status="RESERVED",
    )

    assert len(reservations) >= 1
    assert any(
        reservation["reward_id"] == reward_id
        for reservation in reservations
    )


async def test_list_funding_reservations_without_filters():
    tenant_code = unique_tenant_code("LIST_ALL_TENANT")
    reward_id = unique_reward_id("REWARD-LIST-ALL")

    account, transaction, _, _ = await _create_reserved_funding_transaction(
        tenant_code=tenant_code,
        reward_id=reward_id,
        amount="80.00",
    )

    await create_funding_reservation(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=account["account_id"],
        amount=Decimal("80.00"),
        funding_transaction_id=transaction["transaction_id"],
    )

    reservations = await list_funding_reservations(limit=100)

    assert len(reservations) >= 1
    assert any(
        reservation["reward_id"] == reward_id
        for reservation in reservations
    )