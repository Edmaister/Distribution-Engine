from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


def review_payload(review_id: str, distributor_id: str, **overrides):
    payload = {
        "review_id": review_id,
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "distributor_code": "AGENCY_001",
        "review_type": "KYB",
        "review_status": "OPEN",
        "review_result": None,
        "reviewer": "ops@example.com",
        "notes": "Initial review",
        "metadata": {"source": "test"},
        "reviewed_at": None,
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


def dispute_payload(dispute_id: str, route_id: str, distributor_id: str, **overrides):
    payload = {
        "dispute_id": dispute_id,
        "tenant_code": "FNB",
        "route_id": route_id,
        "opportunity_id": str(uuid4()),
        "distributor_id": distributor_id,
        "raised_by": "AGENCY_001",
        "reason_code": "COMMISSION_QUERY",
        "description": "Commission amount disputed",
        "dispute_status": "OPEN",
        "resolution_notes": None,
        "resolved_by": None,
        "resolved_at": None,
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


def audit_payload(audit_id: str, distributor_id: str, **overrides):
    payload = {
        "audit_id": audit_id,
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "route_id": None,
        "dispute_id": None,
        "compliance_review_id": None,
        "action_type": "SUSPEND",
        "reason_code": "COMPLIANCE_HOLD",
        "actor": "ops@example.com",
        "notes": "Suspended for review",
        "before_state": {"status": "ACTIVE"},
        "after_state": {"status": "SUSPENDED"},
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


async def test_create_compliance_review(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    review_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_create_compliance_review(**kwargs):
        calls.update(kwargs)
        return review_payload(review_id, distributor_id)

    monkeypatch.setattr(
        admin_governance,
        "create_compliance_review",
        fake_create_compliance_review,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/governance/compliance-reviews",
            json={
                "distributor_id": distributor_id,
                "review_type": "KYB",
                "reviewer": "ops@example.com",
                "notes": "Initial review",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    assert response.json()["review_id"] == review_id
    assert calls == {
        "distributor_id": distributor_id,
        "review_type": "KYB",
        "reviewer": "ops@example.com",
        "notes": "Initial review",
        "metadata": {"source": "test"},
    }


async def test_list_compliance_reviews(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    review_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_list_compliance_reviews(**kwargs):
        calls.update(kwargs)
        return [review_payload(review_id, distributor_id)]

    monkeypatch.setattr(
        admin_governance,
        "list_compliance_reviews",
        fake_list_compliance_reviews,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/governance/compliance-reviews",
            params={
                "tenant_code": "FNB",
                "distributor_id": distributor_id,
                "review_status": "OPEN",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["review_id"] == review_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "review_status": "OPEN",
        "limit": 25,
    }


async def test_complete_compliance_review(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    review_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_complete_compliance_review(**kwargs):
        calls.update(kwargs)
        return review_payload(
            review_id,
            distributor_id,
            review_status="COMPLETED",
            review_result="PASSED",
            reviewed_at="2026-06-12T10:05:00",
        )

    monkeypatch.setattr(
        admin_governance,
        "complete_compliance_review",
        fake_complete_compliance_review,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/governance/compliance-reviews/{review_id}/complete",
            json={
                "review_result": "PASSED",
                "reviewer": "ops@example.com",
                "notes": "Approved",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    assert response.json()["review_status"] == "COMPLETED"
    assert calls == {
        "review_id": review_id,
        "review_result": "PASSED",
        "reviewer": "ops@example.com",
        "notes": "Approved",
        "metadata": {"source": "test"},
    }


async def test_create_dispute(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    dispute_id = str(uuid4())
    route_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_create_dispute(**kwargs):
        calls.update(kwargs)
        return dispute_payload(dispute_id, route_id, distributor_id)

    monkeypatch.setattr(admin_governance, "create_dispute", fake_create_dispute)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/governance/disputes",
            json={
                "route_id": route_id,
                "raised_by": "AGENCY_001",
                "reason_code": "COMMISSION_QUERY",
                "description": "Commission amount disputed",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    assert response.json()["dispute_id"] == dispute_id
    assert calls == {
        "route_id": route_id,
        "raised_by": "AGENCY_001",
        "reason_code": "COMMISSION_QUERY",
        "description": "Commission amount disputed",
        "metadata": {"source": "test"},
    }


async def test_list_disputes(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    dispute_id = str(uuid4())
    route_id = str(uuid4())
    distributor_id = str(uuid4())
    opportunity_id = str(uuid4())
    calls = {}

    async def fake_list_disputes(**kwargs):
        calls.update(kwargs)
        return [
            dispute_payload(
                dispute_id,
                route_id,
                distributor_id,
                opportunity_id=opportunity_id,
            )
        ]

    monkeypatch.setattr(admin_governance, "list_disputes", fake_list_disputes)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/governance/disputes",
            params={
                "tenant_code": "FNB",
                "distributor_id": distributor_id,
                "opportunity_id": opportunity_id,
                "dispute_status": "OPEN",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["dispute_id"] == dispute_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "opportunity_id": opportunity_id,
        "dispute_status": "OPEN",
        "limit": 25,
    }


async def test_resolve_dispute(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    dispute_id = str(uuid4())
    route_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_resolve_dispute(**kwargs):
        calls.update(kwargs)
        return dispute_payload(
            dispute_id,
            route_id,
            distributor_id,
            dispute_status="RESOLVED",
            resolved_by="ops@example.com",
            resolution_notes="Paid correctly",
            resolved_at="2026-06-12T10:10:00",
        )

    monkeypatch.setattr(admin_governance, "resolve_dispute", fake_resolve_dispute)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/governance/disputes/{dispute_id}/resolve",
            json={
                "dispute_status": "RESOLVED",
                "resolved_by": "ops@example.com",
                "resolution_notes": "Paid correctly",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    assert response.json()["dispute_status"] == "RESOLVED"
    assert calls == {
        "dispute_id": dispute_id,
        "dispute_status": "RESOLVED",
        "resolved_by": "ops@example.com",
        "resolution_notes": "Paid correctly",
        "metadata": {"source": "test"},
    }


async def test_apply_distributor_governance_action(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    distributor_id = str(uuid4())
    audit_id = str(uuid4())
    calls = {}

    async def fake_apply_distributor_governance_action(**kwargs):
        calls.update(kwargs)
        return {
            "distributor": {
                "distributor_id": distributor_id,
                "tenant_code": "FNB",
                "status": "SUSPENDED",
            },
            "audit": audit_payload(audit_id, distributor_id),
        }

    monkeypatch.setattr(
        admin_governance,
        "apply_distributor_governance_action",
        fake_apply_distributor_governance_action,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/governance/distributors/{distributor_id}/actions",
            json={
                "action_type": "SUSPEND",
                "reason_code": "COMPLIANCE_HOLD",
                "actor": "ops@example.com",
                "notes": "Suspended for review",
                "operating_limits": {"daily_leads": 0},
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["distributor"]["status"] == "SUSPENDED"
    assert body["audit"]["audit_id"] == audit_id
    assert calls == {
        "distributor_id": distributor_id,
        "action_type": "SUSPEND",
        "reason_code": "COMPLIANCE_HOLD",
        "actor": "ops@example.com",
        "notes": "Suspended for review",
        "operating_limits": {"daily_leads": 0},
        "metadata": {"source": "test"},
    }


async def test_list_governance_audit(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    distributor_id = str(uuid4())
    audit_id = str(uuid4())
    calls = {}

    async def fake_list_governance_audit(**kwargs):
        calls.update(kwargs)
        return [audit_payload(audit_id, distributor_id)]

    monkeypatch.setattr(
        admin_governance,
        "list_governance_audit",
        fake_list_governance_audit,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/governance/audit",
            params={
                "tenant_code": "FNB",
                "distributor_id": distributor_id,
                "action_type": "SUSPEND",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["audit_id"] == audit_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "action_type": "SUSPEND",
        "limit": 25,
    }


async def test_governance_not_found_returns_404(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    async def fake_create_compliance_review(**kwargs):
        raise admin_governance.GovernanceNotFound("Distributor not found")

    monkeypatch.setattr(
        admin_governance,
        "create_compliance_review",
        fake_create_compliance_review,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/governance/compliance-reviews",
            json={"distributor_id": str(uuid4()), "review_type": "KYB"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Distributor not found"}


async def test_invalid_governance_action_returns_409(monkeypatch):
    from apps.api.routers.distribution import admin_governance

    async def fake_apply_distributor_governance_action(**kwargs):
        raise admin_governance.GovernanceInvalidAction(
            "Unsupported governance action"
        )

    monkeypatch.setattr(
        admin_governance,
        "apply_distributor_governance_action",
        fake_apply_distributor_governance_action,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/governance/distributors/{uuid4()}/actions",
            json={"action_type": "FREEZE"},
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "Unsupported governance action"}
