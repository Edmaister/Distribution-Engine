from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.exposure import (
    get_or_create_daily_exposure,
    increase_reserved_exposure,
    list_funding_exposure,
    release_exposure,
    settle_exposure,
)

pytestmark = pytest.mark.asyncio


async def test_get_or_create_daily_exposure():
    account_id = uuid4()
    exposure_date = date.today()

    created = await get_or_create_daily_exposure(
        tenant_code="FNB",
        account_id=account_id,
        exposure_date=exposure_date,
    )

    assert created["tenant_code"] == "FNB"
    assert created["account_id"] == account_id
    assert created["exposure_date"] == exposure_date
    assert created["reserved_amount"] == Decimal("0.00")
    assert created["settled_amount"] == Decimal("0.00")
    assert created["released_amount"] == Decimal("0.00")

    fetched = await get_or_create_daily_exposure(
        tenant_code="FNB",
        account_id=account_id,
        exposure_date=exposure_date,
    )

    assert fetched["exposure_id"] == created["exposure_id"]


async def test_increase_reserved_exposure():
    account_id = uuid4()

    first = await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("100.00"),
    )

    second = await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("50.00"),
    )

    assert first["reserved_amount"] == Decimal("100.00")
    assert second["reserved_amount"] == Decimal("150.00")


async def test_settle_exposure_moves_reserved_to_settled():
    account_id = uuid4()

    await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("200.00"),
    )

    settled = await settle_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("75.00"),
    )

    assert settled["reserved_amount"] == Decimal("125.00")
    assert settled["settled_amount"] == Decimal("75.00")


async def test_release_exposure_moves_reserved_to_released():
    account_id = uuid4()

    await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("200.00"),
    )

    released = await release_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("60.00"),
    )

    assert released["reserved_amount"] == Decimal("140.00")
    assert released["released_amount"] == Decimal("60.00")


async def test_settle_and_release_do_not_make_reserved_negative():
    account_id = uuid4()

    settled = await settle_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("999.00"),
    )

    assert settled["reserved_amount"] == Decimal("0.00")
    assert settled["settled_amount"] == Decimal("999.00")

    released = await release_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("999.00"),
    )

    assert released["reserved_amount"] == Decimal("0.00")
    assert released["released_amount"] == Decimal("999.00")


async def test_list_funding_exposure():
    account_id = uuid4()

    created = await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("100.00"),
    )

    rows = await list_funding_exposure(
        tenant_code="FNB",
        account_id=account_id,
    )

    assert len(rows) >= 1
    assert any(row["exposure_id"] == created["exposure_id"] for row in rows)