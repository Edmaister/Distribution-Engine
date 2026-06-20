from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_create_reversal(monkeypatch):
    reversal_id = str(uuid4())
    settlement_id = str(uuid4())
    captured = {}
    audit_calls = []

    async def fake_create_settlement_reversal(**kwargs):
        captured.update(kwargs)
        return {
            "reversal_id": reversal_id,
            "settlement_id": settlement_id,
            "tenant_code": "FNB",
            "reversal_reason": "Duplicate settlement",
            "amount": Decimal("100.00"),
            "status": "REQUESTED",
            "requested_by": "ops-user",
            "approved_by": None,
            "correlation_id": "corr-1",
            "created_at": None,
            "approved_at": None,
            "executed_at": None,
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.create_settlement_reversal",
        fake_create_settlement_reversal,
    )

    async def fake_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.try_write_admin_audit",
        fake_audit,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/settlement/reversals",
            json={
                "settlement_id": settlement_id,
                "tenant_code": "FNB",
                "reversal_reason": "Duplicate settlement",
                "amount": "100.00",
                "requested_by": "ops-user",
                "correlation_id": "corr-1",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"]["reversal_id"] == reversal_id
    assert captured == {
        "settlement_id": settlement_id,
        "tenant_code": "FNB",
        "reversal_reason": "Duplicate settlement",
        "amount": Decimal("100.00"),
        "requested_by": "ops-user",
        "correlation_id": "corr-1",
    }
    assert audit_calls[0]["action_type"] == "SETTLEMENT_REVERSAL_CREATE"
    assert audit_calls[0]["target_id"] == reversal_id
    assert audit_calls[0]["correlation_id"] == "corr-1"


@pytest.mark.asyncio
async def test_get_reversals(monkeypatch):
    reversal_id = str(uuid4())
    settlement_id = str(uuid4())
    captured = {}

    async def fake_list_settlement_reversals(**kwargs):
        captured.update(kwargs)
        return [
            {
                "reversal_id": reversal_id,
                "settlement_id": settlement_id,
                "tenant_code": "FNB",
                "reversal_reason": "Duplicate settlement",
                "amount": Decimal("100.00"),
                "status": "REQUESTED",
                "requested_by": "ops-user",
                "approved_by": None,
                "correlation_id": "corr-1",
                "created_at": None,
                "approved_at": None,
                "executed_at": None,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.list_settlement_reversals",
        fake_list_settlement_reversals,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/settlement/reversals",
            params={
                "tenant_code": "FNB",
                "settlement_id": settlement_id,
                "status": "REQUESTED",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["reversal_id"] == reversal_id
    assert captured == {
        "tenant_code": "FNB",
        "settlement_id": settlement_id,
        "status": "REQUESTED",
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_reversal(monkeypatch):
    reversal_id = str(uuid4())

    async def fake_get_settlement_reversal(*, reversal_id):
        return {
            "reversal_id": reversal_id,
            "settlement_id": str(uuid4()),
            "tenant_code": "FNB",
            "reversal_reason": "Incorrect amount",
            "amount": Decimal("250.00"),
            "status": "REQUESTED",
            "requested_by": "ops-user",
            "approved_by": None,
            "correlation_id": None,
            "created_at": None,
            "approved_at": None,
            "executed_at": None,
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.get_settlement_reversal",
        fake_get_settlement_reversal,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/settlement/reversals/{reversal_id}"
        )

    assert response.status_code == 200
    assert response.json()["item"]["reversal_id"] == reversal_id


@pytest.mark.asyncio
async def test_get_reversal_not_found(monkeypatch):
    async def fake_get_settlement_reversal(*, reversal_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.get_settlement_reversal",
        fake_get_settlement_reversal,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/settlement/reversals/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Settlement reversal not found"
    }


@pytest.mark.asyncio
async def test_approve_reversal(monkeypatch):
    reversal_id = str(uuid4())
    captured = {}

    async def fake_approve_settlement_reversal(**kwargs):
        captured.update(kwargs)
        return {
            "reversal_id": reversal_id,
            "status": "APPROVED",
            "approved_by": "finance-user",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.approve_settlement_reversal",
        fake_approve_settlement_reversal,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/reversals/{reversal_id}/approve",
            json={"approved_by": "finance-user"},
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "APPROVED"
    assert captured == {
        "reversal_id": reversal_id,
        "approved_by": "finance-user",
    }


@pytest.mark.asyncio
async def test_approve_reversal_invalid(monkeypatch):
    async def fake_approve_settlement_reversal(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.approve_settlement_reversal",
        fake_approve_settlement_reversal,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/reversals/{uuid4()}/approve",
            json={"approved_by": "finance-user"},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement reversal cannot be approved"
    }


@pytest.mark.asyncio
async def test_execute_reversal(monkeypatch):
    reversal_id = str(uuid4())

    async def fake_execute_settlement_reversal(*, reversal_id):
        return {
            "reversal_id": reversal_id,
            "status": "EXECUTED",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.execute_settlement_reversal",
        fake_execute_settlement_reversal,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/reversals/{reversal_id}/execute"
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "EXECUTED"


@pytest.mark.asyncio
async def test_execute_reversal_invalid(monkeypatch):
    async def fake_execute_settlement_reversal(*, reversal_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_reversals.execute_settlement_reversal",
        fake_execute_settlement_reversal,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/reversals/{uuid4()}/execute"
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement reversal cannot be executed"
    }
