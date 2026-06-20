from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_get_settlement_exceptions(monkeypatch):
    exception_id = str(uuid4())
    batch_id = str(uuid4())
    settlement_id = str(uuid4())
    captured = {}

    async def fake_list_settlement_exceptions(**kwargs):
        captured.update(kwargs)
        return [
            {
                "exception_id": exception_id,
                "batch_id": batch_id,
                "settlement_id": settlement_id,
                "exception_type": "BATCH_AMOUNT_VARIANCE",
                "severity": "WARNING",
                "status": "OPEN",
                "exception_message": "Batch amount variance.",
                "correlation_id": "corr-1",
                "created_at": None,
                "resolved_at": None,
                "resolved_by": None,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_exceptions.list_settlement_exceptions",
        fake_list_settlement_exceptions,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/settlement/exceptions",
            params={
                "batch_id": batch_id,
                "settlement_id": settlement_id,
                "status": "OPEN",
                "severity": "WARNING",
                "exception_type": "BATCH_AMOUNT_VARIANCE",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["items"][0]["exception_id"] == exception_id

    assert captured == {
        "batch_id": batch_id,
        "settlement_id": settlement_id,
        "status": "OPEN",
        "severity": "WARNING",
        "exception_type": "BATCH_AMOUNT_VARIANCE",
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_exception(monkeypatch):
    exception_id = str(uuid4())

    async def fake_get_settlement_exception(*, exception_id):
        return {
            "exception_id": exception_id,
            "batch_id": str(uuid4()),
            "settlement_id": str(uuid4()),
            "exception_type": "DUPLICATE_SETTLEMENT",
            "severity": "CRITICAL",
            "status": "OPEN",
            "exception_message": "Duplicate settlement detected.",
            "correlation_id": None,
            "created_at": None,
            "resolved_at": None,
            "resolved_by": None,
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_exceptions.get_settlement_exception",
        fake_get_settlement_exception,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/settlement/exceptions/{exception_id}"
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["item"]["exception_id"] == exception_id


@pytest.mark.asyncio
async def test_get_exception_not_found(monkeypatch):
    async def fake_get_settlement_exception(*, exception_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_exceptions.get_settlement_exception",
        fake_get_settlement_exception,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/settlement/exceptions/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Settlement exception not found"
    }


@pytest.mark.asyncio
async def test_resolve_exception(monkeypatch):
    exception_id = str(uuid4())
    captured = {}

    async def fake_resolve_settlement_exception(**kwargs):
        captured.update(kwargs)
        return {
            "exception_id": exception_id,
            "status": "RESOLVED",
            "resolved_by": "ops-user",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_exceptions.resolve_settlement_exception",
        fake_resolve_settlement_exception,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/exceptions/{exception_id}/resolve",
            json={"resolved_by": "ops-user"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "item": {
            "exception_id": exception_id,
            "status": "RESOLVED",
            "resolved_by": "ops-user",
        },
    }

    assert captured == {
        "exception_id": exception_id,
        "resolved_by": "ops-user",
    }


@pytest.mark.asyncio
async def test_resolve_exception_not_found(monkeypatch):
    async def fake_resolve_settlement_exception(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_exceptions.resolve_settlement_exception",
        fake_resolve_settlement_exception,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/exceptions/{uuid4()}/resolve",
            json={"resolved_by": "ops-user"},
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Settlement exception not found or already resolved"
    }
