from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


@pytest.mark.asyncio
async def test_request_approval(monkeypatch):
    batch_id = str(uuid4())
    approval_id = str(uuid4())
    captured = {}

    async def fake_request_batch_approval(**kwargs):
        captured.update(kwargs)
        return {
            "approval_id": approval_id,
            "batch_id": batch_id,
            "approval_type": "SETTLEMENT_BATCH_APPROVAL",
            "approval_status": "PENDING",
            "requested_by": "maker-user",
            "approved_by": None,
            "comments": "Please approve",
            "created_at": None,
            "approved_at": None,
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.request_batch_approval",
        fake_request_batch_approval,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{batch_id}/approval/request",
            json={
                "approval_type": "SETTLEMENT_BATCH_APPROVAL",
                "requested_by": "maker-user",
                "comments": "Please approve",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"]["approval_id"] == approval_id
    assert captured == {
        "batch_id": batch_id,
        "approval_type": "SETTLEMENT_BATCH_APPROVAL",
        "requested_by": "maker-user",
        "comments": "Please approve",
    }


@pytest.mark.asyncio
async def test_request_approval_invalid(monkeypatch):
    async def fake_request_batch_approval(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.request_batch_approval",
        fake_request_batch_approval,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/batches/{uuid4()}/approval/request",
            json={
                "requested_by": "maker-user",
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement batch approval cannot be requested"
    }


@pytest.mark.asyncio
async def test_approve_approval(monkeypatch):
    approval_id = str(uuid4())
    captured = {}
    audit_calls = []

    async def fake_approve_batch_request(**kwargs):
        captured.update(kwargs)
        return {
            "approval_id": approval_id,
            "approval_status": "APPROVED",
            "approved_by": "checker-user",
            "comments": "Approved",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.approve_batch_request",
        fake_approve_batch_request,
    )

    async def fake_audit(**kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.try_write_admin_audit",
        fake_audit,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/approvals/{approval_id}/approve",
            json={
                "approved_by": "checker-user",
                "comments": "Approved",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"]["approval_status"] == "APPROVED"
    assert captured == {
        "approval_id": approval_id,
        "approved_by": "checker-user",
        "comments": "Approved",
    }
    assert audit_calls[0]["action_type"] == "SETTLEMENT_APPROVAL_APPROVE"
    assert audit_calls[0]["target_id"] == approval_id


@pytest.mark.asyncio
async def test_approve_approval_invalid(monkeypatch):
    async def fake_approve_batch_request(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.approve_batch_request",
        fake_approve_batch_request,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/approvals/{uuid4()}/approve",
            json={
                "approved_by": "checker-user",
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement approval cannot be approved"
    }


@pytest.mark.asyncio
async def test_reject_approval(monkeypatch):
    approval_id = str(uuid4())
    captured = {}

    async def fake_reject_batch_request(**kwargs):
        captured.update(kwargs)
        return {
            "approval_id": approval_id,
            "approval_status": "REJECTED",
            "approved_by": "checker-user",
            "comments": "Rejected",
        }

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.reject_batch_request",
        fake_reject_batch_request,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/approvals/{approval_id}/reject",
            json={
                "rejected_by": "checker-user",
                "comments": "Rejected",
            },
        )

    assert response.status_code == 200
    assert response.json()["item"]["approval_status"] == "REJECTED"
    assert captured == {
        "approval_id": approval_id,
        "rejected_by": "checker-user",
        "comments": "Rejected",
    }


@pytest.mark.asyncio
async def test_reject_approval_invalid(monkeypatch):
    async def fake_reject_batch_request(**kwargs):
        return None

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.reject_batch_request",
        fake_reject_batch_request,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/settlement/approvals/{uuid4()}/reject",
            json={
                "rejected_by": "checker-user",
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Settlement approval cannot be rejected"
    }


@pytest.mark.asyncio
async def test_get_approvals(monkeypatch):
    batch_id = str(uuid4())
    approval_id = str(uuid4())
    captured = {}

    async def fake_get_batch_approvals(**kwargs):
        captured.update(kwargs)
        return [
            {
                "approval_id": approval_id,
                "batch_id": batch_id,
                "approval_type": "SETTLEMENT_BATCH_APPROVAL",
                "approval_status": "PENDING",
                "requested_by": "maker-user",
                "approved_by": None,
                "comments": None,
                "created_at": None,
                "approved_at": None,
            }
        ]

    monkeypatch.setattr(
        "apps.api.routers.admin_settlement_approvals.get_batch_approvals",
        fake_get_batch_approvals,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/settlement/batches/{batch_id}/approvals"
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["approval_id"] == approval_id
    assert captured == {"batch_id": batch_id}
