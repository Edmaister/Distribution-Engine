from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
from services.funding.resolution_audit import (
    create_funding_resolution_audit,
)

pytestmark = pytest.mark.asyncio


async def test_get_funding_audit():
    tenant_code = f"FNB-{uuid4()}"

    await create_funding_resolution_audit(
        reward_id=f"REWARD-{uuid4()}",
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

    async with AsyncClient(
        app=app,
        base_url="http://test", headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/admin/funding/audit",
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] >= 1
    assert isinstance(body["items"], list)


async def test_get_funding_audit_filtered_by_tenant():
    tenant_code = f"FILTER-{uuid4()}"

    await create_funding_resolution_audit(
        reward_id=f"REWARD-{uuid4()}",
        tenant_code=tenant_code,
        account_id=uuid4(),
        rule_id=uuid4(),
        reward_type="REFERRAL",
        segment_code="PRIVATE",
        campaign_code="TEST",
        sponsor_code="FNB",
        amount=Decimal("250.00"),
        correlation_id=f"CORR-{uuid4()}",
    )

    async with AsyncClient(
        app=app,
        base_url="http://test", headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/admin/funding/audit",
            params={
                "tenant_code": tenant_code,
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"

    for item in body["items"]:
        assert item["tenant_code"] == tenant_code


async def test_get_funding_audit_limit():
    async with AsyncClient(
        app=app,
        base_url="http://test", headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/admin/funding/audit",
            params={
                "limit": 1,
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert len(body["items"]) <= 1
