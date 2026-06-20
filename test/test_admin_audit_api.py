from __future__ import annotations

from fastapi.testclient import TestClient

import apps.api.routers.admin_audit as router
from apps.api.main import app


client = TestClient(app)


def test_admin_audit_list_requires_admin_key():
    response = client.get("/admin/audit")

    assert response.status_code == 401


def test_admin_audit_list_accepts_system_admin_key(monkeypatch):
    calls = []

    async def fake_list_admin_audit(**kwargs):
        calls.append(kwargs)
        return [
            {
                "admin_audit_id": "audit-1",
                "action_domain": "FINANCE",
                "action_type": "FX_RATE_UPSERT",
                "action_status": "SUCCESS",
            }
        ]

    monkeypatch.setattr(router, "list_admin_audit", fake_list_admin_audit)

    response = client.get(
        "/admin/audit",
        headers={"x-api-key": "test-system-admin-key"},
        params={
            "action_domain": "FINANCE",
            "action_type": "FX_RATE_UPSERT",
            "tenant_code": "FNB",
            "target_type": "fx_rate",
            "target_id": "fx-123",
            "limit": 25,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "count": 1,
        "items": [
            {
                "admin_audit_id": "audit-1",
                "action_domain": "FINANCE",
                "action_type": "FX_RATE_UPSERT",
                "action_status": "SUCCESS",
            }
        ],
    }
    assert calls == [
        {
            "action_domain": "FINANCE",
            "action_type": "FX_RATE_UPSERT",
            "tenant_code": "FNB",
            "target_type": "fx_rate",
            "target_id": "fx-123",
            "limit": 25,
        }
    ]


def test_admin_audit_summary_accepts_platform_admin_key(monkeypatch):
    calls = []

    async def fake_get_admin_audit_summary(**kwargs):
        calls.append(kwargs)
        return {
            "window_hours": 12,
            "action_domain": "DISTRIBUTION",
            "tenant_code": "FNB",
            "total": 3,
            "by_domain": [{"action_domain": "DISTRIBUTION", "count": 3}],
            "by_status": [{"action_status": "SUCCESS", "count": 3}],
            "top_actions": [{"action_type": "DISTRIBUTOR_CREATE", "count": 3}],
        }

    monkeypatch.setattr(router, "get_admin_audit_summary", fake_get_admin_audit_summary)

    response = client.get(
        "/admin/audit/summary",
        headers={"x-api-key": "test-admin-key"},
        params={
            "action_domain": "DISTRIBUTION",
            "tenant_code": "FNB",
            "hours": 12,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["summary"]["total"] == 3
    assert calls == [
        {
            "action_domain": "DISTRIBUTION",
            "tenant_code": "FNB",
            "hours": 12,
        }
    ]


def test_admin_audit_rejects_wrong_scoped_admin_key(monkeypatch):
    async def fake_get_admin_audit_summary(**kwargs):
        return {"total": 0}

    monkeypatch.setattr(router, "get_admin_audit_summary", fake_get_admin_audit_summary)

    response = client.get(
        "/admin/audit/summary",
        headers={"x-api-key": "test-finance-admin-key"},
    )

    assert response.status_code == 403
