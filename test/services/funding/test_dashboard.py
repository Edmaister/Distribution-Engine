from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.dashboard import (
    _decimal,
    _empty_summary,
    get_account_funding_summary,
    get_funding_summary,
    get_tenant_funding_summary,
)
from services.funding.exposure import increase_reserved_exposure, settle_exposure
from services.funding.limits import create_funding_limit

pytestmark = pytest.mark.asyncio


def test_decimal_handles_none_and_value():
    assert _decimal(None) == Decimal("0.00")
    assert _decimal("10.50") == Decimal("10.50")
    assert _decimal(Decimal("5.25")) == Decimal("5.25")


def test_empty_summary_defaults():
    summary = _empty_summary()

    assert summary["daily_limit"] == Decimal("0.00")
    assert summary["daily_used"] == Decimal("0.00")
    assert summary["monthly_limit"] == Decimal("0.00")
    assert summary["monthly_used"] == Decimal("0.00")
    assert summary["exposure_limit"] == Decimal("0.00")
    assert summary["current_exposure"] == Decimal("0.00")


async def test_get_account_funding_summary_without_limit_or_exposure():
    account_id = uuid4()

    summary = await get_account_funding_summary(
        tenant_code="FNB",
        account_id=account_id,
    )

    assert summary["tenant_code"] == "FNB"
    assert summary["account_id"] == str(account_id)
    assert summary["daily_limit"] == Decimal("0.00")
    assert summary["monthly_limit"] == Decimal("0.00")
    assert summary["exposure_limit"] == Decimal("0.00")
    assert summary["daily_used"] == Decimal("0.00")
    assert summary["monthly_used"] == Decimal("0.00")
    assert summary["current_exposure"] == Decimal("0.00")


async def test_get_account_funding_summary_with_limit_and_exposure():
    account_id = uuid4()
    if date.today().day == 1:
        same_month_date = date.today().replace(day=2)
    else:
        same_month_date = date.today().replace(day=1)

    await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("10000.00"),
    )

    await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("100.00"),
        exposure_date=date.today(),
    )

    await settle_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("25.00"),
        exposure_date=date.today(),
    )

    await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("50.00"),
        exposure_date=same_month_date,
    )

    summary = await get_account_funding_summary(
        tenant_code="FNB",
        account_id=account_id,
    )

    assert summary["daily_limit"] == Decimal("1000.00")
    assert summary["monthly_limit"] == Decimal("5000.00")
    assert summary["exposure_limit"] == Decimal("10000.00")
    assert summary["daily_used"] == Decimal("100.00")
    assert summary["monthly_used"] == Decimal("150.00")
    assert summary["current_exposure"] == Decimal("150.00")


async def test_get_tenant_funding_summary_empty():
    summary = await get_tenant_funding_summary(
        tenant_code=f"EMPTY-{uuid4()}",
    )

    assert summary["account_count"] == 0
    assert summary["daily_used"] == Decimal("0.00")
    assert summary["monthly_used"] == Decimal("0.00")
    assert summary["current_exposure"] == Decimal("0.00")


async def test_get_tenant_funding_summary_with_multiple_accounts():
    tenant_code = f"FNB-{uuid4()}"
    account_one = uuid4()
    account_two = uuid4()
    if date.today().day == 1:
        same_month_date = date.today().replace(day=2)
    else:
        same_month_date = date.today().replace(day=1)

    await increase_reserved_exposure(
        tenant_code=tenant_code,
        account_id=account_one,
        amount=Decimal("100.00"),
        exposure_date=date.today(),
    )

    await increase_reserved_exposure(
        tenant_code=tenant_code,
        account_id=account_two,
        amount=Decimal("200.00"),
        exposure_date=same_month_date,
    )

    summary = await get_tenant_funding_summary(
        tenant_code=tenant_code,
    )

    assert summary["tenant_code"] == tenant_code
    assert summary["account_count"] == 2
    assert summary["daily_used"] == Decimal("100.00")
    assert summary["monthly_used"] == Decimal("300.00")
    assert summary["current_exposure"] == Decimal("300.00")


async def test_get_funding_summary():
    tenant_code = f"FNB-{uuid4()}"
    account_id = uuid4()

    await increase_reserved_exposure(
        tenant_code=tenant_code,
        account_id=account_id,
        amount=Decimal("123.00"),
        exposure_date=date.today(),
    )

    summary = await get_funding_summary()

    assert summary["tenant_count"] >= 1
    assert summary["account_count"] >= 1
    assert summary["current_exposure"] >= Decimal("123.00")