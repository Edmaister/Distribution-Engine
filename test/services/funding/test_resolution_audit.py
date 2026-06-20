from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from services.funding.resolution_audit import (
    create_funding_resolution_audit,
    list_funding_resolution_audit,
)

pytestmark = pytest.mark.asyncio


async def test_create_and_list_funding_resolution_audit():
    tenant_code = f"FNB-{uuid4()}"
    reward_id = f"REWARD-{uuid4()}"

    await create_funding_resolution_audit(
        reward_id=reward_id,
        tenant_code=tenant_code,
        account_id=uuid4(),
        rule_id=uuid4(),
        reward_type="REFERRAL",
        segment_code="PERSONAL",
        campaign_code="BURGER_FRIDAY",
        sponsor_code="FNB",
        amount=Decimal("100.00"),
        correlation_id=f"CORR-{uuid4()}",
    )

    items = await list_funding_resolution_audit(
        tenant_code=tenant_code,
    )

    assert len(items) >= 1

    record = next(
        item for item in items
        if item["reward_id"] == reward_id
    )

    assert record["tenant_code"] == tenant_code
    assert record["reward_type"] == "REFERRAL"
    assert record["segment_code"] == "PERSONAL"
    assert record["campaign_code"] == "BURGER_FRIDAY"
    assert record["sponsor_code"] == "FNB"


async def test_list_funding_resolution_audit_filters_by_tenant():
    tenant_one = f"TENANT1-{uuid4()}"
    tenant_two = f"TENANT2-{uuid4()}"

    await create_funding_resolution_audit(
        reward_id=f"R1-{uuid4()}",
        tenant_code=tenant_one,
        account_id=uuid4(),
        rule_id=None,
        reward_type=None,
        segment_code=None,
        campaign_code=None,
        sponsor_code=None,
        amount=Decimal("50.00"),
        correlation_id=None,
    )

    await create_funding_resolution_audit(
        reward_id=f"R2-{uuid4()}",
        tenant_code=tenant_two,
        account_id=uuid4(),
        rule_id=None,
        reward_type=None,
        segment_code=None,
        campaign_code=None,
        sponsor_code=None,
        amount=Decimal("75.00"),
        correlation_id=None,
    )

    items = await list_funding_resolution_audit(
        tenant_code=tenant_one,
    )

    assert len(items) >= 1

    for item in items:
        assert item["tenant_code"] == tenant_one


async def test_list_funding_resolution_audit_limit():
    tenant_code = f"LIMIT-{uuid4()}"

    for i in range(3):
        await create_funding_resolution_audit(
            reward_id=f"R-{i}-{uuid4()}",
            tenant_code=tenant_code,
            account_id=uuid4(),
            rule_id=None,
            reward_type=None,
            segment_code=None,
            campaign_code=None,
            sponsor_code=None,
            amount=Decimal("10.00"),
            correlation_id=None,
        )

    items = await list_funding_resolution_audit(
        tenant_code=tenant_code,
        limit=2,
    )

    assert len(items) <= 2