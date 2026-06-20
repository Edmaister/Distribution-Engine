from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.limits import (
    create_funding_limit,
    get_active_funding_limit,
    list_funding_limits,
    update_funding_limit,
)

pytestmark = pytest.mark.asyncio


async def test_create_and_get_active_funding_limit():
    account_id = uuid4()

    created = await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("10000.00"),
        exposure_limit=Decimal("20000.00"),
    )

    assert created["tenant_code"] == "FNB"
    assert created["account_id"] == account_id
    assert created["daily_limit"] == Decimal("1000.00")
    assert created["monthly_limit"] == Decimal("10000.00")
    assert created["exposure_limit"] == Decimal("20000.00")
    assert created["is_active"] is True

    fetched = await get_active_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
    )

    assert fetched is not None
    assert fetched["limit_id"] == created["limit_id"]


async def test_update_funding_limit():
    account_id = uuid4()

    created = await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("10000.00"),
        exposure_limit=Decimal("20000.00"),
    )

    updated = await update_funding_limit(
        limit_id=created["limit_id"],
        daily_limit=Decimal("1500.00"),
        monthly_limit=Decimal("12000.00"),
        exposure_limit=Decimal("25000.00"),
        is_active=False,
    )

    assert updated is not None
    assert updated["daily_limit"] == Decimal("1500.00")
    assert updated["monthly_limit"] == Decimal("12000.00")
    assert updated["exposure_limit"] == Decimal("25000.00")
    assert updated["is_active"] is False

    active = await get_active_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
    )

    assert active is None


async def test_update_missing_limit_returns_none():
    updated = await update_funding_limit(
        limit_id=uuid4(),
        daily_limit=Decimal("1.00"),
    )

    assert updated is None


async def test_list_funding_limits():
    account_id = uuid4()

    created = await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("500.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("8000.00"),
    )

    rows = await list_funding_limits(
        tenant_code="FNB",
        account_id=account_id,
    )

    assert len(rows) >= 1
    assert any(row["limit_id"] == created["limit_id"] for row in rows)