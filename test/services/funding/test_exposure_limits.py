from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.exposure import increase_reserved_exposure
from services.funding.exposure_limits import validate_exposure
from services.funding.limits import create_funding_limit

pytestmark = pytest.mark.asyncio


async def test_validate_exposure_allows_within_limits():
    account_id = uuid4()

    await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("10000.00"),
    )

    valid, reason = await validate_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("250.00"),
    )

    assert valid is True
    assert reason is None


async def test_validate_exposure_fails_without_active_limit():
    valid, reason = await validate_exposure(
        tenant_code="FNB",
        account_id=uuid4(),
        amount=Decimal("250.00"),
    )

    assert valid is False
    assert reason == "NO_ACTIVE_LIMIT"


async def test_validate_exposure_fails_daily_limit():
    account_id = uuid4()

    await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("100.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("10000.00"),
    )

    await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("80.00"),
        exposure_date=date.today(),
    )

    valid, reason = await validate_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("30.00"),
    )

    assert valid is False
    assert reason == "DAILY_LIMIT_EXCEEDED"


async def test_validate_exposure_fails_monthly_limit():
    account_id = uuid4()

    if date.today().day == 1:
        same_month_date = date.today().replace(day=2)
    else:
        same_month_date = date.today().replace(day=1)

    await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("100.00"),
        exposure_limit=Decimal("10000.00"),
    )

    await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("80.00"),
        exposure_date=same_month_date,
    )

    valid, reason = await validate_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("30.00"),
    )

    assert valid is False
    assert reason == "MONTHLY_LIMIT_EXCEEDED"


async def test_validate_exposure_fails_exposure_limit():
    account_id = uuid4()

    await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("100.00"),
    )

    await increase_reserved_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("80.00"),
        exposure_date=date.today() - timedelta(days=40),
    )

    valid, reason = await validate_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("30.00"),
    )

    assert valid is False
    assert reason == "EXPOSURE_LIMIT_EXCEEDED"

async def test_validate_exposure_handles_null_values():
    account_id = uuid4()

    await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("10000.00"),
    )

    valid, reason = await validate_exposure(
        tenant_code="FNB",
        account_id=account_id,
        amount=Decimal("1.00"),
    )

    assert valid is True
    assert reason is None