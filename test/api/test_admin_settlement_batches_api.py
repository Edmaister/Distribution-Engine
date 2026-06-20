from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_create_batch(monkeypatch):
    batch_id = str(uuid4())
    captured = {}

    async def fake_create_settlement_batch(**kwargs):
        captured.update(kwargs)
        return {
            "batch_id": batch_id,
            "tenant_code": "FNB",
            "batch_reference": "BATCH-001",
            "batch_type": "REWARD_SETTLEMENT",
            "status": "DRAFT",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.create_settlement_batch",
        fake_create_settlement_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/settlement/batches",
            json={
                "tenant_code": "FNB",
                "batch_reference": "BATCH-001",
                "batch_type": "REWARD_SETTLEMENT",
                "created_by": "admin",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"]["batch_id"] == batch_id
    assert captured == {
        "tenant_code": "FNB",
        "batch_reference": "BATCH-001",
        "batch_type": "REWARD_SETTLEMENT",
        "created_by": "admin",
    }


@pytest.mark.asyncio
async def test_add_item_to_batch(monkeypatch):
    batch_id = str(uuid4())
    settlement_id = str(uuid4())
    captured = {}

    async def fake_add_settlement_to_batch(**kwargs):
        captured.update(kwargs)
        return {
            "item": {
                "batch_item_id": str(uuid4()),
                "batch_id": batch_id,
                "settlement_id": settlement_id,
                "amount": Decimal("100.00"),
                "status": "ADDED",
            },
            "batch": {
                "batch_id": batch_id,
                "status": "DRAFT",
                "total_count": 1,
                "total_amount": Decimal("100.00"),
            },
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.add_settlement_to_batch",
        fake_add_settlement_to_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{batch_id}/items",
            json={
                "settlement_id": settlement_id,
                "amount": "100.00",
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["item"]["settlement_id"] == settlement_id
    assert captured["batch_id"] == batch_id
    assert captured["settlement_id"] == settlement_id
    assert captured["amount"] == Decimal("100.00")


@pytest.mark.asyncio
async def test_add_item_to_batch_not_found(monkeypatch):
    async def fake_add_settlement_to_batch(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.add_settlement_to_batch",
        fake_add_settlement_to_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{uuid4()}/items",
            json={
                "settlement_id": str(uuid4()),
                "amount": "100.00",
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Settlement batch not found or not editable"
    }


@pytest.mark.asyncio
async def test_submit_batch(monkeypatch):
    batch_id = str(uuid4())

    async def fake_submit_batch_for_approval(*, batch_id):
        return {
            "batch_id": batch_id,
            "status": "READY_FOR_APPROVAL",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.submit_batch_for_approval",
        fake_submit_batch_for_approval,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{batch_id}/submit"
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "READY_FOR_APPROVAL"


@pytest.mark.asyncio
async def test_submit_batch_invalid(monkeypatch):
    async def fake_submit_batch_for_approval(*, batch_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.submit_batch_for_approval",
        fake_submit_batch_for_approval,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{uuid4()}/submit"
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement batch cannot be submitted"
    }


@pytest.mark.asyncio
async def test_approve_settlement_batch(monkeypatch):
    batch_id = str(uuid4())
    captured = {}

    async def fake_approve_batch(**kwargs):
        captured.update(kwargs)
        return {
            "batch_id": batch_id,
            "status": "APPROVED",
            "approved_by": "finance-user",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.approve_batch",
        fake_approve_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{batch_id}/approve",
            json={"approved_by": "finance-user"},
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "APPROVED"
    assert captured == {
        "batch_id": batch_id,
        "approved_by": "finance-user",
    }


@pytest.mark.asyncio
async def test_approve_settlement_batch_invalid(monkeypatch):
    async def fake_approve_batch(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.approve_batch",
        fake_approve_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{uuid4()}/approve",
            json={"approved_by": "finance-user"},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement batch cannot be approved"
    }


@pytest.mark.asyncio
async def test_execute_settlement_batch(monkeypatch):
    batch_id = str(uuid4())

    async def fake_execute_batch(*, batch_id):
        return {
            "batch_id": batch_id,
            "status": "SETTLED",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.execute_batch",
        fake_execute_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{batch_id}/execute"
        )

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "SETTLED"


@pytest.mark.asyncio
async def test_execute_settlement_batch_invalid(monkeypatch):
    async def fake_execute_batch(*, batch_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.execute_batch",
        fake_execute_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{uuid4()}/execute"
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement batch cannot be executed"
    }


@pytest.mark.asyncio
async def test_get_batches(monkeypatch):
    batch_id = str(uuid4())
    captured = {}

    async def fake_list_settlement_batches(**kwargs):
        captured.update(kwargs)
        return [
            {
                "batch_id": batch_id,
                "tenant_code": "FNB",
                "status": "DRAFT",
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.list_settlement_batches",
        fake_list_settlement_batches,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/settlement/batches",
            params={
                "tenant_code": "FNB",
                "status": "DRAFT",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert captured == {
        "tenant_code": "FNB",
        "status": "DRAFT",
        "limit": 25,
    }


@pytest.mark.asyncio
async def test_get_batch(monkeypatch):
    batch_id = str(uuid4())

    async def fake_get_settlement_batch(*, batch_id):
        return {
            "batch": {
                "batch_id": batch_id,
                "tenant_code": "FNB",
                "status": "DRAFT",
            },
            "item_count": 0,
            "items": [],
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.get_settlement_batch",
        fake_get_settlement_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/settlement/batches/{batch_id}"
        )

    assert response.status_code == 200
    assert response.json()["batch"]["batch_id"] == batch_id


@pytest.mark.asyncio
async def test_get_batch_not_found(monkeypatch):
    async def fake_get_settlement_batch(*, batch_id):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_batches.get_settlement_batch",
        fake_get_settlement_batch,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/settlement/batches/{uuid4()}"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Settlement batch not found"
    }
