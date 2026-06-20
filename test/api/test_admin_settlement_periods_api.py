from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_create_period(monkeypatch):
    period_id = str(uuid4())
    captured = {}

    async def fake_create_settlement_period(**kwargs):
        captured.update(kwargs)
        return {
            "period_id": period_id,
            "tenant_code": "FNB",
            "period_code": "2026-06",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "status": "OPEN",
            "created_by": "finance-user",
            "closed_by": None,
            "created_at": None,
            "closed_at": None,
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.create_settlement_period",
        fake_create_settlement_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/settlement/periods",
            json={
                "tenant_code": "FNB",
                "period_code": "2026-06",
                "period_start": "2026-06-01",
                "period_end": "2026-06-30",
                "created_by": "finance-user",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"]["period_id"] == period_id
    assert captured == {
        "tenant_code": "FNB",
        "period_code": "2026-06",
        "period_start": "2026-06-01",
        "period_end": "2026-06-30",
        "created_by": "finance-user",
    }


@pytest.mark.asyncio
async def test_get_periods(monkeypatch):
    period_id = str(uuid4())
    captured = {}

    async def fake_list_settlement_periods(**kwargs):
        captured.update(kwargs)
        return [
            {
                "period_id": period_id,
                "tenant_code": "FNB",
                "period_code": "2026-06",
                "status": "OPEN",
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.list_settlement_periods",
        fake_list_settlement_periods,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/settlement/periods",
            params={
                "tenant_code": "FNB",
                "status": "OPEN",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert captured == {
        "tenant_code": "FNB",
        "status": "OPEN",
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_current_period(monkeypatch):
    period_id = str(uuid4())
    captured = {}

    async def fake_get_current_open_period(**kwargs):
        captured.update(kwargs)
        return {
            "period_id": period_id,
            "tenant_code": "FNB",
            "period_code": "2026-06",
            "status": "OPEN",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.get_current_open_period",
        fake_get_current_open_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/settlement/periods/current",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200
    assert response.json()["item"]["period_id"] == period_id
    assert captured == {"tenant_code": "FNB"}


@pytest.mark.asyncio
async def test_get_current_period_not_found(monkeypatch):
    async def fake_get_current_open_period(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.get_current_open_period",
        fake_get_current_open_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get("/admin/settlement/periods/current")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No open settlement period found"
    }


@pytest.mark.asyncio
async def test_get_period(monkeypatch):
    period_id = str(uuid4())

    async def fake_get_settlement_period(*, period_id):
        return {
            "period_id": period_id,
            "tenant_code": "FNB",
            "period_code": "2026-06",
            "status": "OPEN",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.get_settlement_period",
        fake_get_settlement_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/settlement/periods/{period_id}")

    assert response.status_code == 200
    assert response.json()["item"]["period_id"] == period_id


@pytest.mark.asyncio
async def test_get_period_not_found(monkeypatch):
    async def fake_get_settlement_period(*, period_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.get_settlement_period",
        fake_get_settlement_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/settlement/periods/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Settlement period not found"
    }


@pytest.mark.asyncio
async def test_close_period(monkeypatch):
    period_id = str(uuid4())
    captured = {}

    async def fake_close_settlement_period(**kwargs):
        captured.update(kwargs)
        return {
            "period_id": period_id,
            "status": "CLOSED",
            "closed_by": "treasury-user",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.close_settlement_period",
        fake_close_settlement_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/periods/{period_id}/close",
            json={"closed_by": "treasury-user"},
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "CLOSED"
    assert captured == {
        "period_id": period_id,
        "closed_by": "treasury-user",
    }


@pytest.mark.asyncio
async def test_close_period_invalid(monkeypatch):
    async def fake_close_settlement_period(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.close_settlement_period",
        fake_close_settlement_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/periods/{uuid4()}/close",
            json={"closed_by": "treasury-user"},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement period cannot be closed"
    }


@pytest.mark.asyncio
async def test_reopen_period(monkeypatch):
    period_id = str(uuid4())

    async def fake_reopen_settlement_period(*, period_id):
        return {
            "period_id": period_id,
            "status": "OPEN",
            "closed_by": None,
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.reopen_settlement_period",
        fake_reopen_settlement_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/periods/{period_id}/reopen"
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "OPEN"


@pytest.mark.asyncio
async def test_reopen_period_invalid(monkeypatch):
    async def fake_reopen_settlement_period(*, period_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_periods.reopen_settlement_period",
        fake_reopen_settlement_period,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/periods/{uuid4()}/reopen"
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement period cannot be reopened"
    }
