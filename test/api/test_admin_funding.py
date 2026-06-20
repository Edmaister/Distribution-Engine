from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
from services.funding.exposure import increase_reserved_exposure
from services.funding.limits import create_funding_limit

pytestmark = pytest.mark.asyncio


async def test_get_funding_exposure_empty():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/admin/funding/exposure")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] >= 0
    assert isinstance(body["items"], list)


async def test_get_funding_limits_empty_or_existing():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/admin/funding/limits")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] >= 0
    assert isinstance(body["items"], list)


async def test_post_funding_limit():
    account_id = str(uuid4())

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/limits",
            json={
                "tenant_code": "FNB",
                "account_id": account_id,
                "daily_limit": "1000.00",
                "monthly_limit": "5000.00",
                "exposure_limit": "10000.00",
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "created"
    assert body["item"]["tenant_code"] == "FNB"
    assert body["item"]["account_id"] == account_id
    assert body["item"]["daily_limit"] == "1000.00"
    assert body["item"]["monthly_limit"] == "5000.00"
    assert body["item"]["exposure_limit"] == "10000.00"
    assert body["item"]["is_active"] is True


async def test_put_funding_limit_updates_record():
    account_id = uuid4()

    created = await create_funding_limit(
        tenant_code="FNB",
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("10000.00"),
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            f"/admin/funding/limits/{created['limit_id']}",
            json={
                "daily_limit": "1500.00",
                "monthly_limit": "6000.00",
                "exposure_limit": "12000.00",
                "is_active": False,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "updated"
    assert body["item"]["daily_limit"] == "1500.00"
    assert body["item"]["monthly_limit"] == "6000.00"
    assert body["item"]["exposure_limit"] == "12000.00"
    assert body["item"]["is_active"] is False


async def test_put_funding_limit_not_found():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.put(
            f"/admin/funding/limits/{uuid4()}",
            json={"daily_limit": "1500.00"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Funding limit not found"


async def test_post_funding_limit_validation_error():
    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/limits",
            json={
                "tenant_code": "",
                "account_id": str(uuid4()),
                "daily_limit": "1000.00",
                "monthly_limit": "5000.00",
                "exposure_limit": "10000.00",
            },
        )

    assert response.status_code == 422


async def test_get_platform_funding_dashboard():
    tenant_code = f"FNB-{uuid4()}"
    account_id = uuid4()

    await increase_reserved_exposure(
        tenant_code=tenant_code,
        account_id=account_id,
        amount=Decimal("123.00"),
        exposure_date=date.today(),
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/admin/funding/dashboard")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["summary"]["tenant_count"] >= 1
    assert body["summary"]["account_count"] >= 1
    assert Decimal(str(body["summary"]["current_exposure"])) >= Decimal("123.00")


async def test_get_tenant_funding_dashboard_empty():
    tenant_code = f"EMPTY-{uuid4()}"

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/funding/dashboard/{tenant_code}")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["summary"]["tenant_code"] == tenant_code
    assert body["summary"]["account_count"] == 0
    assert body["summary"]["daily_used"] == "0.00"
    assert body["summary"]["monthly_used"] == "0.00"
    assert body["summary"]["current_exposure"] == "0.00"


async def test_get_tenant_funding_dashboard_with_exposure():
    tenant_code = f"FNB-{uuid4()}"
    account_one = uuid4()
    account_two = uuid4()

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
        exposure_date=date.today(),
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/funding/dashboard/{tenant_code}")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["summary"]["tenant_code"] == tenant_code
    assert body["summary"]["account_count"] == 2
    assert body["summary"]["daily_used"] == "300.00"
    assert body["summary"]["monthly_used"] == "300.00"
    assert body["summary"]["current_exposure"] == "300.00"


async def test_get_account_funding_dashboard_without_limit_or_exposure():
    tenant_code = f"FNB-{uuid4()}"
    account_id = uuid4()

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/dashboard/{tenant_code}/{account_id}"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["summary"]["tenant_code"] == tenant_code
    assert body["summary"]["account_id"] == str(account_id)
    assert body["summary"]["daily_limit"] == "0.00"
    assert body["summary"]["daily_used"] == "0.00"
    assert body["summary"]["monthly_limit"] == "0.00"
    assert body["summary"]["monthly_used"] == "0.00"
    assert body["summary"]["exposure_limit"] == "0.00"
    assert body["summary"]["current_exposure"] == "0.00"


async def test_get_account_funding_dashboard_with_limit_and_exposure():
    tenant_code = f"FNB-{uuid4()}"
    account_id = uuid4()

    await create_funding_limit(
        tenant_code=tenant_code,
        account_id=account_id,
        daily_limit=Decimal("1000.00"),
        monthly_limit=Decimal("5000.00"),
        exposure_limit=Decimal("10000.00"),
    )

    await increase_reserved_exposure(
        tenant_code=tenant_code,
        account_id=account_id,
        amount=Decimal("250.00"),
        exposure_date=date.today(),
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/dashboard/{tenant_code}/{account_id}"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["summary"]["tenant_code"] == tenant_code
    assert body["summary"]["account_id"] == str(account_id)
    assert body["summary"]["daily_limit"] == "1000.00"
    assert body["summary"]["daily_used"] == "250.00"
    assert body["summary"]["monthly_limit"] == "5000.00"
    assert body["summary"]["monthly_used"] == "250.00"
    assert body["summary"]["exposure_limit"] == "10000.00"
    assert body["summary"]["current_exposure"] == "250.00"


async def test_get_account_funding_dashboard_invalid_uuid():
    tenant_code = f"FNB-{uuid4()}"

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/dashboard/{tenant_code}/not-a-valid-uuid"
        )

    assert response.status_code == 422
