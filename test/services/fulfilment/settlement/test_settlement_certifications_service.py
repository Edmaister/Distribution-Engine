from __future__ import annotations

from decimal import Decimal
from datetime import date
from uuid import uuid4

import pytest

from services.fulfilment.settlement.certifications import (
    certify_settlement_period,
    create_settlement_certification,
    get_settlement_certification,
    list_settlement_certifications,
)
from services.fulfilment.settlement.periods import create_settlement_period


def unique_tenant() -> str:
    return f"TEST_{uuid4().hex[:8]}"


async def create_test_period(tenant_code: str) -> str:
    period = await create_settlement_period(
        tenant_code=tenant_code,
        period_code=f"TEST-{uuid4().hex[:8]}",
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 31),
        created_by="pytest",
    )

    return str(period["period_id"])


@pytest.mark.asyncio
async def test_create_get_list_and_certify_settlement_certification():
    tenant_code = unique_tenant()
    period_id = await create_test_period(tenant_code)

    created = await create_settlement_certification(
        tenant_code=tenant_code,
        period_id=period_id,
        expected_amount=Decimal("1000.00"),
        actual_amount=Decimal("999.50"),
    )

    assert created["tenant_code"] == tenant_code
    assert str(created["period_id"]) == period_id
    assert created["expected_amount"] == Decimal("1000.00")
    assert created["actual_amount"] == Decimal("999.50")
    assert created["variance_amount"] == Decimal("-0.50")
    assert created["status"] == "PENDING"

    certification_id = str(created["certification_id"])

    fetched = await get_settlement_certification(certification_id)

    assert fetched is not None
    assert str(fetched["certification_id"]) == certification_id
    assert fetched["tenant_code"] == tenant_code

    listed = await list_settlement_certifications(
        tenant_code=tenant_code,
        limit=10,
    )

    assert len(listed) >= 1
    assert any(str(item["certification_id"]) == certification_id for item in listed)

    certified = await certify_settlement_period(
        certification_id=certification_id,
        certified_by="Treasury User",
        certification_notes="Month-end checked and certified.",
    )

    assert certified is not None
    assert certified["status"] == "CERTIFIED"
    assert certified["certified_by"] == "Treasury User"
    assert certified["certification_notes"] == "Month-end checked and certified."
    assert certified["certified_at"] is not None


@pytest.mark.asyncio
async def test_get_missing_settlement_certification_returns_none():
    result = await get_settlement_certification(str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_certify_missing_settlement_certification_returns_none():
    result = await certify_settlement_period(
        certification_id=str(uuid4()),
        certified_by="Treasury User",
        certification_notes="Missing record.",
    )

    assert result is None


@pytest.mark.asyncio
async def test_list_settlement_certifications_without_tenant_filter():
    tenant_code = unique_tenant()
    period_id = await create_test_period(tenant_code)

    await create_settlement_certification(
        tenant_code=tenant_code,
        period_id=period_id,
        expected_amount=Decimal("500.00"),
        actual_amount=Decimal("500.00"),
    )

    result = await list_settlement_certifications(limit=25)

    assert isinstance(result, list)
    assert len(result) >= 1