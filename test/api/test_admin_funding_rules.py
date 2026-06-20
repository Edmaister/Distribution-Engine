from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
from services.funding.account_rules import create_funding_account_rule
from services.funding_service import create_funding_account

pytestmark = pytest.mark.asyncio


def unique_tenant_code(prefix: str = "TENANT") -> str:
    return f"{prefix}_{uuid4().hex[:8].upper()}"


async def create_test_account(*, tenant_code: str):
    return await create_funding_account(
        tenant_code=tenant_code,
        account_name=f"{tenant_code} Wallet",
        account_type="TENANT_WALLET",
        opening_balance="1000.00",
    )


async def test_get_funding_rules_empty_or_existing():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/admin/funding/rules")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] >= 0
    assert isinstance(body["items"], list)


async def test_post_funding_rule():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/rules",
            json={
                "tenant_code": tenant_code,
                "account_id": str(account["account_id"]),
                "reward_type": "REFERRAL",
                "segment_code": "PERSONAL",
                "campaign_code": "BURGER_FRIDAY",
                "sponsor_code": "FNB",
                "priority": 10,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "created"
    assert body["item"]["tenant_code"] == tenant_code
    assert body["item"]["account_id"] == str(account["account_id"])
    assert body["item"]["reward_type"] == "REFERRAL"
    assert body["item"]["segment_code"] == "PERSONAL"
    assert body["item"]["campaign_code"] == "BURGER_FRIDAY"
    assert body["item"]["sponsor_code"] == "FNB"
    assert body["item"]["priority"] == 10
    assert body["item"]["is_active"] is True


async def test_get_funding_rule_by_id():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    rule = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="REFERRAL",
        priority=20,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/funding/rules/{rule['rule_id']}")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["item"]["rule_id"] == str(rule["rule_id"])
    assert body["item"]["tenant_code"] == tenant_code
    assert body["item"]["priority"] == 20


async def test_get_funding_rule_not_found():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/funding/rules/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Funding rule not found"


async def test_put_funding_rule_updates_record():
    tenant_code = unique_tenant_code("FNB")
    account = await create_test_account(tenant_code=tenant_code)

    rule = await create_funding_account_rule(
        tenant_code=tenant_code,
        account_id=account["account_id"],
        reward_type="REFERRAL",
        priority=100,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            f"/admin/funding/rules/{rule['rule_id']}",
            json={
                "reward_type": "CAMPAIGN",
                "segment_code": "PRIVATE",
                "campaign_code": "BLACK_FRIDAY",
                "sponsor_code": "PNP",
                "priority": 5,
                "is_active": False,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "updated"
    assert body["item"]["reward_type"] == "CAMPAIGN"
    assert body["item"]["segment_code"] == "PRIVATE"
    assert body["item"]["campaign_code"] == "BLACK_FRIDAY"
    assert body["item"]["sponsor_code"] == "PNP"
    assert body["item"]["priority"] == 5
    assert body["item"]["is_active"] is False


async def test_put_funding_rule_not_found():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            f"/admin/funding/rules/{uuid4()}",
            json={
                "reward_type": "CAMPAIGN",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Funding rule not found"


