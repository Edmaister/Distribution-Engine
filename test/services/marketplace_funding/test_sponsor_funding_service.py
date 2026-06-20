from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.marketplace_funding.sponsor_funding_service import (
    debit_reward_funding,
    get_allocation_by_reward,
    list_allocations,
    release_reward_funding,
    reserve_reward_funding,
    reverse_reward_funding,
)
from services.marketplace_funding.sponsor_wallet_balance_service import (
    topup_wallet,
)
from services.marketplace_funding.sponsor_wallet_service import (
    create_sponsor_wallet,
)


pytestmark = pytest.mark.asyncio


def unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}".upper()


def unique_uuid() -> str:
    return str(uuid4())


async def create_funded_wallet(
    *,
    tenant_code: str,
    sponsor_code: str,
    amount: Decimal = Decimal("1000.00"),
) -> dict:
    wallet = await create_sponsor_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        sponsor_name=f"{sponsor_code} Test Sponsor",
        currency="ZAR",
    )

    await topup_wallet(
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        amount=amount,
        correlation_id=unique_code("TOPUP"),
        metadata={"test": True},
    )

    return wallet


async def test_reserve_reward_funding_creates_allocation_and_reserves_wallet():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    result = await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("100.00"),
        correlation_id=unique_code("CORR"),
        metadata={"source": "pytest"},
    )

    assert result["reserved"] is True
    assert result["already_reserved"] is False
    assert result["allocation"]["reward_id"] == reward_id
    assert result["allocation"]["wallet_id"] == wallet["wallet_id"]
    assert result["allocation"]["tenant_code"] == tenant_code
    assert result["allocation"]["sponsor_code"] == sponsor_code
    assert result["allocation"]["amount"] == Decimal("100.00")
    assert result["allocation"]["status"] == "RESERVED"


async def test_reserve_reward_funding_is_idempotent_for_existing_reward():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    first = await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("100.00"),
    )

    second = await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("100.00"),
    )

    assert first["reserved"] is True
    assert second["reserved"] is True
    assert second["already_reserved"] is True
    assert second["allocation"]["allocation_id"] == first["allocation"]["allocation_id"]


async def test_get_allocation_by_reward_returns_allocation():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("50.00"),
    )

    allocation = await get_allocation_by_reward(reward_id=reward_id)

    assert allocation is not None
    assert allocation["reward_id"] == reward_id
    assert allocation["status"] == "RESERVED"


async def test_release_reward_funding_releases_reserved_allocation():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("75.00"),
    )

    result = await release_reward_funding(reward_id=reward_id)

    assert result["released"] is True
    assert result["allocation"]["status"] == "RELEASED"
    assert result["allocation"]["released_at"] is not None


async def test_release_reward_funding_is_idempotent_when_already_released():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("75.00"),
    )

    first = await release_reward_funding(reward_id=reward_id)
    second = await release_reward_funding(reward_id=reward_id)

    assert first["released"] is True
    assert second["released"] is True
    assert second["already_released"] is True


async def test_release_reward_funding_returns_not_found_for_missing_allocation():
    result = await release_reward_funding(reward_id=unique_uuid())

    assert result["released"] is False
    assert result["reason"] == "ALLOCATION_NOT_FOUND"


async def test_debit_reward_funding_debits_reserved_allocation():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("120.00"),
    )

    result = await debit_reward_funding(reward_id=reward_id)

    assert result["debited"] is True
    assert result["allocation"]["status"] == "DEBITED"
    assert result["allocation"]["debited_at"] is not None


async def test_debit_reward_funding_is_idempotent_when_already_debited():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("120.00"),
    )

    first = await debit_reward_funding(reward_id=reward_id)
    second = await debit_reward_funding(reward_id=reward_id)

    assert first["debited"] is True
    assert second["debited"] is True
    assert second["already_debited"] is True


async def test_debit_reward_funding_returns_not_found_for_missing_allocation():
    result = await debit_reward_funding(reward_id=unique_uuid())

    assert result["debited"] is False
    assert result["reason"] == "ALLOCATION_NOT_FOUND"


async def test_reverse_reward_funding_reverses_debited_allocation():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("90.00"),
    )

    await debit_reward_funding(reward_id=reward_id)

    result = await reverse_reward_funding(reward_id=reward_id)

    assert result["reversed"] is True
    assert result["allocation"]["status"] == "REVERSED"
    assert result["allocation"]["reversed_at"] is not None


async def test_reverse_reward_funding_is_idempotent_when_already_reversed():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("90.00"),
    )

    await debit_reward_funding(reward_id=reward_id)

    first = await reverse_reward_funding(reward_id=reward_id)
    second = await reverse_reward_funding(reward_id=reward_id)

    assert first["reversed"] is True
    assert second["reversed"] is True
    assert second["already_reversed"] is True


async def test_reverse_reward_funding_returns_invalid_status_when_not_debited():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("90.00"),
    )

    result = await reverse_reward_funding(reward_id=reward_id)

    assert result["reversed"] is False
    assert result["reason"] == "INVALID_STATUS_RESERVED"


async def test_reverse_reward_funding_returns_not_found_for_missing_allocation():
    result = await reverse_reward_funding(reward_id=unique_uuid())

    assert result["reversed"] is False
    assert result["reason"] == "ALLOCATION_NOT_FOUND"


async def test_list_allocations_filters_by_tenant_sponsor_and_status():
    tenant_code = unique_code("TENANT")
    sponsor_code = unique_code("SPONSOR")
    reward_id = unique_uuid()

    wallet = await create_funded_wallet(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
    )

    await reserve_reward_funding(
        reward_id=reward_id,
        wallet_id=str(wallet["wallet_id"]),
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        amount=Decimal("60.00"),
    )

    results = await list_allocations(
        tenant_code=tenant_code,
        sponsor_code=sponsor_code,
        status="RESERVED",
    )

    assert len(results) >= 1
    assert all(row["tenant_code"] == tenant_code for row in results)
    assert all(row["sponsor_code"] == sponsor_code for row in results)
    assert all(row["status"] == "RESERVED" for row in results)