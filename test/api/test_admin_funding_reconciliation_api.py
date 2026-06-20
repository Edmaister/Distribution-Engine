from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_run_reconciliation(monkeypatch):
    captured = {}
    run_id = str(uuid4())

    async def fake_run_funding_reconciliation(
        *,
        tenant_code,
        correlation_id=None,
    ):
        captured["tenant_code"] = tenant_code
        captured["correlation_id"] = correlation_id

        return {
            "status": "ok",
            "run": {
                "run_id": run_id,
                "tenant_code": tenant_code,
                "expected_amount": Decimal("1000000.00"),
                "actual_amount": Decimal("999950.00"),
                "variance_amount": Decimal("-50.00"),
                "status": "EXCEPTION",
                "correlation_id": correlation_id,
                "created_at": None,
            },
            "exception_count": 1,
            "exceptions": [],
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_reconciliation.run_funding_reconciliation",
        fake_run_funding_reconciliation,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/funding/reconciliation/run",
            params={
                "tenant_code": "FNB",
                "correlation_id": "corr-1",
            },
        )

    assert response.status_code == 200
    assert response.json()["run"]["status"] == "EXCEPTION"

    assert captured == {
        "tenant_code": "FNB",
        "correlation_id": "corr-1",
    }


@pytest.mark.asyncio
async def test_get_reconciliation_runs(monkeypatch):
    run_id = str(uuid4())
    captured = {}

    async def fake_list_funding_reconciliation_runs(
        *,
        tenant_code=None,
        status=None,
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["status"] = status
        captured["limit"] = limit

        return [
            {
                "run_id": run_id,
                "tenant_code": "FNB",
                "expected_amount": Decimal("100.00"),
                "actual_amount": Decimal("100.00"),
                "variance_amount": Decimal("0.00"),
                "status": "MATCHED",
                "correlation_id": None,
                "created_at": None,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_reconciliation.list_funding_reconciliation_runs",
        fake_list_funding_reconciliation_runs,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/reconciliation",
            params={
                "tenant_code": "FNB",
                "status": "MATCHED",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["items"][0]["run_id"] == run_id

    assert captured == {
        "tenant_code": "FNB",
        "status": "MATCHED",
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_reconciliation_exceptions(monkeypatch):
    exception_id = str(uuid4())
    captured = {}

    async def fake_list_funding_reconciliation_exceptions(
        *,
        tenant_code=None,
        status="OPEN",
        limit=100,
    ):
        captured["tenant_code"] = tenant_code
        captured["status"] = status
        captured["limit"] = limit

        return [
            {
                "exception_id": exception_id,
                "run_id": str(uuid4()),
                "tenant_code": "FNB",
                "exception_type": "FUNDING_VARIANCE",
                "reference_id": None,
                "expected_amount": Decimal("100.00"),
                "actual_amount": Decimal("90.00"),
                "variance_amount": Decimal("-10.00"),
                "status": "OPEN",
                "correlation_id": None,
                "created_at": None,
                "resolved_at": None,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_reconciliation.list_funding_reconciliation_exceptions",
        fake_list_funding_reconciliation_exceptions,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/funding/reconciliation/exceptions",
            params={
                "tenant_code": "FNB",
                "status": "OPEN",
                "limit": 50,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["count"] == 1
    assert body["items"][0]["exception_id"] == exception_id

    assert captured == {
        "tenant_code": "FNB",
        "status": "OPEN",
        "limit": 50,
    }


@pytest.mark.asyncio
async def test_get_reconciliation_run(monkeypatch):
    run_id = str(uuid4())

    async def fake_get_funding_reconciliation_run(*, run_id):
        return {
            "run": {
                "run_id": run_id,
                "tenant_code": "FNB",
                "expected_amount": Decimal("1000000.00"),
                "actual_amount": Decimal("999950.00"),
                "variance_amount": Decimal("-50.00"),
                "status": "EXCEPTION",
                "correlation_id": None,
                "created_at": None,
            },
            "exception_count": 1,
            "exceptions": [
                {
                    "exception_id": str(uuid4()),
                    "run_id": run_id,
                    "tenant_code": "FNB",
                    "exception_type": "FUNDING_VARIANCE",
                    "status": "OPEN",
                }
            ],
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_reconciliation.get_funding_reconciliation_run",
        fake_get_funding_reconciliation_run,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/reconciliation/{run_id}"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["run"]["run_id"] == run_id
    assert body["exception_count"] == 1


@pytest.mark.asyncio
async def test_get_reconciliation_run_not_found(monkeypatch):
    async def fake_get_funding_reconciliation_run(*, run_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_reconciliation.get_funding_reconciliation_run",
        fake_get_funding_reconciliation_run,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/funding/reconciliation/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Funding reconciliation run not found"
    }


@pytest.mark.asyncio
async def test_resolve_reconciliation_exception(monkeypatch):
    exception_id = str(uuid4())

    async def fake_resolve_funding_reconciliation_exception(*, exception_id):
        return {
            "exception_id": exception_id,
            "run_id": str(uuid4()),
            "tenant_code": "FNB",
            "exception_type": "FUNDING_VARIANCE",
            "status": "RESOLVED",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_reconciliation.resolve_funding_reconciliation_exception",
        fake_resolve_funding_reconciliation_exception,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/reconciliation/exceptions/{exception_id}/resolve"
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "RESOLVED"


@pytest.mark.asyncio
async def test_resolve_reconciliation_exception_not_found(monkeypatch):
    async def fake_resolve_funding_reconciliation_exception(*, exception_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_funding_reconciliation.resolve_funding_reconciliation_exception",
        fake_resolve_funding_reconciliation_exception,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/funding/reconciliation/exceptions/{uuid4()}/resolve"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Funding reconciliation exception not found or already resolved"
    }
