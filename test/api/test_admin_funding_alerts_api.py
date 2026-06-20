from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_get_funding_alerts(monkeypatch):
    alert_id = str(uuid4())
    account_id = str(uuid4())
    captured = {}

    async def fake_list_funding_alerts(
        *,
        tenant_code=None,
        account_id=None,
        status="OPEN",
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["account_id"] = account_id
        captured["status"] = status
        captured["limit"] = limit

        return [
            {
                "alert_id": alert_id,
                "tenant_code": "FNB",
                "account_id": account_id,
                "alert_type": "FUNDING_LOW",
                "severity": "WARNING",
                "alert_message": "Funding account is low.",
                "status": "OPEN",
                "correlation_id": "corr-1",
                "created_at": None,
                "acknowledged_at": None,
                "resolved_at": None,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_alerts.list_funding_alerts",
        fake_list_funding_alerts,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/alerts",
            params={
                "tenant_code": "FNB",
                "account_id": account_id,
                "status": "OPEN",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["items"][0]["alert_id"] == alert_id

    assert captured == {
        "tenant_code": "FNB",
        "account_id": account_id,
        "status": "OPEN",
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_funding_alerts_for_account(monkeypatch):
    alert_id = str(uuid4())
    account_id = str(uuid4())
    captured = {}

    async def fake_list_funding_alerts(
        *,
        tenant_code=None,
        account_id=None,
        status="OPEN",
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["account_id"] = account_id
        captured["status"] = status
        captured["limit"] = limit

        return [
            {
                "alert_id": alert_id,
                "tenant_code": "FNB",
                "account_id": account_id,
                "alert_type": "FUNDING_CRITICAL",
                "severity": "CRITICAL",
                "alert_message": "Funding account is critical.",
                "status": "OPEN",
                "correlation_id": None,
                "created_at": None,
                "acknowledged_at": None,
                "resolved_at": None,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_alerts.list_funding_alerts",
        fake_list_funding_alerts,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/alerts/{account_id}",
            params={
                "status": "OPEN",
                "limit": 50,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["account_id"] == account_id
    assert body["count"] == 1
    assert body["items"][0]["alert_type"] == "FUNDING_CRITICAL"

    assert captured == {
        "tenant_code": None,
        "account_id": account_id,
        "status": "OPEN",
        "limit": 50,
    }


@pytest.mark.asyncio
async def test_run_funding_alert_evaluation(monkeypatch):
    captured = {}

    async def fake_evaluate_funding_alerts(
        *,
        tenant_code=None,
        burn_window_days=30,
        buffer_days=30,
        limit=100,
        correlation_id=None,
    ):
        captured["tenant_code"] = tenant_code
        captured["burn_window_days"] = burn_window_days
        captured["buffer_days"] = buffer_days
        captured["limit"] = limit
        captured["correlation_id"] = correlation_id

        return {
            "status": "ok",
            "evaluated_count": 1,
            "alert_count": 1,
            "items": [
                {
                    "alert_type": "FUNDING_LOW",
                    "severity": "WARNING",
                }
            ],
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_alerts.evaluate_funding_alerts",
        fake_evaluate_funding_alerts,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/alerts/run",
            params={
                "tenant_code": "FNB",
                "burn_window_days": 60,
                "buffer_days": 45,
                "limit": 20,
                "correlation_id": "corr-1",
            },
        )

    assert response.status_code == 200
    assert response.json()["alert_count"] == 1

    assert captured == {
        "tenant_code": "FNB",
        "burn_window_days": 60,
        "buffer_days": 45,
        "limit": 20,
        "correlation_id": "corr-1",
    }


@pytest.mark.asyncio
async def test_acknowledge_alert(monkeypatch):
    alert_id = str(uuid4())

    async def fake_acknowledge_funding_alert(*, alert_id):
        return {
            "alert_id": alert_id,
            "tenant_code": "FNB",
            "status": "ACKNOWLEDGED",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_alerts.acknowledge_funding_alert",
        fake_acknowledge_funding_alert,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/alerts/{alert_id}/acknowledge"
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "item": {
            "alert_id": alert_id,
            "tenant_code": "FNB",
            "status": "ACKNOWLEDGED",
        },
    }


@pytest.mark.asyncio
async def test_acknowledge_alert_not_found(monkeypatch):
    async def fake_acknowledge_funding_alert(*, alert_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_alerts.acknowledge_funding_alert",
        fake_acknowledge_funding_alert,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/alerts/{uuid4()}/acknowledge"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Funding alert not found or not open"
    }


@pytest.mark.asyncio
async def test_resolve_alert(monkeypatch):
    alert_id = str(uuid4())

    async def fake_resolve_funding_alert(*, alert_id):
        return {
            "alert_id": alert_id,
            "tenant_code": "FNB",
            "status": "RESOLVED",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_alerts.resolve_funding_alert",
        fake_resolve_funding_alert,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/alerts/{alert_id}/resolve"
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "RESOLVED"


@pytest.mark.asyncio
async def test_resolve_alert_not_found(monkeypatch):
    async def fake_resolve_funding_alert(*, alert_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_alerts.resolve_funding_alert",
        fake_resolve_funding_alert,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/alerts/{uuid4()}/resolve"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Funding alert not found or already resolved"
    }
