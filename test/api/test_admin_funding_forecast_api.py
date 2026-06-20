from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_get_all_funding_forecasts(monkeypatch):
    captured: dict = {}

    async def fake_list_funding_forecasts(
        *,
        tenant_code=None,
        burn_window_days=30,
        buffer_days=30,
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["burn_window_days"] = burn_window_days
        captured["buffer_days"] = buffer_days
        captured["limit"] = limit

        return [
            {
                "account_id": str(uuid4()),
                "tenant_code": "FNB",
                "account_name": "Main Rewards Funding",
                "account_type": "REWARD_POOL",
                "currency": "ZAR",
                "account_status": "ACTIVE",
                "current_balance": Decimal("5000000.00"),
                "reserved_amount": Decimal("200000.00"),
                "available_balance": Decimal("4800000.00"),
                "burn_window_days": 30,
                "buffer_days": 30,
                "total_burn": Decimal("3600000.00"),
                "average_burn_rate_per_day": Decimal("120000.00"),
                "days_remaining": Decimal("40.00"),
                "target_buffer": Decimal("3600000.00"),
                "funding_required": Decimal("0.00"),
                "recommended_top_up": Decimal("0.00"),
                "status": "HEALTHY",
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.list_funding_forecasts",
        fake_list_funding_forecasts,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test", headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/admin/funding/forecast",
            params={
                "tenant_code": "FNB",
                "burn_window_days": 60,
                "buffer_days": 45,
                "limit": 25,
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["tenant_code"] == "FNB"
    assert body["items"][0]["status"] == "HEALTHY"
    assert body["items"][0]["current_balance"] == 5000000.0
    assert body["items"][0]["average_burn_rate_per_day"] == 120000.0

    assert captured == {
        "tenant_code": "FNB",
        "burn_window_days": 60,
        "buffer_days": 45,
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_all_funding_forecasts_defaults(monkeypatch):
    captured: dict = {}

    async def fake_list_funding_forecasts(
        *,
        tenant_code=None,
        burn_window_days=30,
        buffer_days=30,
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["burn_window_days"] = burn_window_days
        captured["buffer_days"] = buffer_days
        captured["limit"] = limit
        return []

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.list_funding_forecasts",
        fake_list_funding_forecasts,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test", headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get("/admin/funding/forecast")

    assert response.status_code == 200

    body = response.json()

    assert body == {
        "status": "ok",
        "count": 0,
        "items": [],
    }

    assert captured == {
        "tenant_code": None,
        "burn_window_days": 30,
        "buffer_days": 30,
        "limit": 100,
    }


@pytest.mark.asyncio
async def test_get_single_funding_forecast(monkeypatch):
    account_id = str(uuid4())
    captured: dict = {}

    async def fake_get_funding_forecast(
        *,
        account_id,
        burn_window_days=30,
        buffer_days=30,
    ):
        captured["account_id"] = account_id
        captured["burn_window_days"] = burn_window_days
        captured["buffer_days"] = buffer_days

        return {
            "account_id": account_id,
            "tenant_code": "FNB",
            "account_name": "Main Rewards Funding",
            "account_type": "REWARD_POOL",
            "currency": "ZAR",
            "account_status": "ACTIVE",
            "current_balance": Decimal("5000000.00"),
            "reserved_amount": Decimal("200000.00"),
            "available_balance": Decimal("4800000.00"),
            "burn_window_days": 30,
            "buffer_days": 30,
            "total_burn": Decimal("3600000.00"),
            "average_burn_rate_per_day": Decimal("120000.00"),
            "days_remaining": Decimal("40.00"),
            "target_buffer": Decimal("3600000.00"),
            "funding_required": Decimal("0.00"),
            "recommended_top_up": Decimal("0.00"),
            "status": "HEALTHY",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.get_funding_forecast",
        fake_get_funding_forecast,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test", headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            f"/admin/funding/forecast/{account_id}",
            params={
                "burn_window_days": 60,
                "buffer_days": 45,
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["item"]["account_id"] == account_id
    assert body["item"]["tenant_code"] == "FNB"
    assert body["item"]["status"] == "HEALTHY"
    assert body["item"]["current_balance"] == 5000000.0

    assert captured == {
        "account_id": account_id,
        "burn_window_days": 60,
        "buffer_days": 45,
    }


@pytest.mark.asyncio
async def test_get_single_funding_forecast_not_found(monkeypatch):
    account_id = str(uuid4())

    async def fake_get_funding_forecast(
        *,
        account_id,
        burn_window_days=30,
        buffer_days=30,
    ):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.get_funding_forecast",
        fake_get_funding_forecast,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test", headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(f"/admin/funding/forecast/{account_id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Funding account not found",
    }


@pytest.mark.asyncio
async def test_get_all_sponsor_funding_forecasts(monkeypatch):
    captured: dict = {}

    async def fake_list_sponsor_funding_forecasts(
        *,
        tenant_code=None,
        sponsor_code=None,
        currency="ZAR",
        burn_window_days=30,
        buffer_days=30,
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["sponsor_code"] = sponsor_code
        captured["currency"] = currency
        captured["burn_window_days"] = burn_window_days
        captured["buffer_days"] = buffer_days
        captured["limit"] = limit

        return [
            {
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "sponsor_name": "Boxer",
                "currency": "ZAR",
                "wallet": {
                    "available_balance": Decimal("900000.00"),
                    "average_burn_rate_per_day": Decimal("10000.00"),
                    "forecast_status": "HEALTHY",
                },
                "contracts": {
                    "count": 1,
                    "remaining_amount": Decimal("1250000.00"),
                    "forecast_status": "HEALTHY",
                    "items": [],
                },
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.list_sponsor_funding_forecasts",
        fake_list_sponsor_funding_forecasts,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/admin/funding/sponsor-forecast",
            params={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "currency": "ZAR",
                "burn_window_days": 60,
                "buffer_days": 45,
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["items"][0]["sponsor_code"] == "BOXER"
    assert body["items"][0]["wallet"]["available_balance"] == 900000.0
    assert captured == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "currency": "ZAR",
        "burn_window_days": 60,
        "buffer_days": 45,
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_single_sponsor_funding_forecast(monkeypatch):
    captured: dict = {}

    async def fake_get_sponsor_funding_forecast(
        *,
        tenant_code,
        sponsor_code,
        currency="ZAR",
        burn_window_days=30,
        buffer_days=30,
    ):
        captured["tenant_code"] = tenant_code
        captured["sponsor_code"] = sponsor_code
        captured["currency"] = currency
        captured["burn_window_days"] = burn_window_days
        captured["buffer_days"] = buffer_days

        return {
            "tenant_code": tenant_code.upper(),
            "sponsor_code": sponsor_code.upper(),
            "currency": currency.upper(),
            "wallet": {
                "available_balance": Decimal("900000.00"),
                "forecast_status": "HEALTHY",
            },
            "contracts": {"count": 0, "items": []},
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.get_sponsor_funding_forecast",
        fake_get_sponsor_funding_forecast,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/admin/funding/sponsor-forecast/FNB/BOXER",
            params={"burn_window_days": 60, "buffer_days": 45},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["item"]["tenant_code"] == "FNB"
    assert body["item"]["sponsor_code"] == "BOXER"
    assert captured == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "currency": "ZAR",
        "burn_window_days": 60,
        "buffer_days": 45,
    }


@pytest.mark.asyncio
async def test_get_single_sponsor_funding_forecast_not_found(monkeypatch):
    async def fake_get_sponsor_funding_forecast(
        *,
        tenant_code,
        sponsor_code,
        currency="ZAR",
        burn_window_days=30,
        buffer_days=30,
    ):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.get_sponsor_funding_forecast",
        fake_get_sponsor_funding_forecast,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get("/admin/funding/sponsor-forecast/FNB/BOXER")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Sponsor funding forecast not found",
    }


@pytest.mark.asyncio
async def test_get_settlement_exposure_forecasts(monkeypatch):
    captured: dict = {}

    async def fake_list_settlement_exposure_forecasts(
        *,
        tenant_code=None,
        provider_key=None,
        currency=None,
        burn_window_days=30,
        buffer_days=30,
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["provider_key"] = provider_key
        captured["currency"] = currency
        captured["burn_window_days"] = burn_window_days
        captured["buffer_days"] = buffer_days
        captured["limit"] = limit

        return [
            {
                "tenant_code": "FNB",
                "provider_key": "CASH_PROVIDER",
                "currency": "ZAR",
                "open_settlement_count": 4,
                "current_exposure_amount": Decimal("4000.00"),
                "settled_amount": Decimal("3000.00"),
                "average_settlement_rate_per_day": Decimal("100.00"),
                "projected_settlement_amount": Decimal("1500.00"),
                "projected_total_exposure": Decimal("5500.00"),
                "forecast_status": "CRITICAL",
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_forecast.list_settlement_exposure_forecasts",
        fake_list_settlement_exposure_forecasts,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers=ADMIN_HEADERS,
    ) as client:
        response = await client.get(
            "/admin/funding/settlement-exposure-forecast",
            params={
                "tenant_code": "FNB",
                "provider_key": "CASH_PROVIDER",
                "currency": "ZAR",
                "burn_window_days": 60,
                "buffer_days": 15,
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["items"][0]["provider_key"] == "CASH_PROVIDER"
    assert body["items"][0]["projected_total_exposure"] == 5500.0
    assert captured == {
        "tenant_code": "FNB",
        "provider_key": "CASH_PROVIDER",
        "currency": "ZAR",
        "burn_window_days": 60,
        "buffer_days": 15,
        "limit": 25,
    }
