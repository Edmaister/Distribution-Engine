from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.admin_experience as admin_experience
from utils.security import require_system_admin_key


def _admin_identity():
    return {"tenant_code": "INTERNAL", "role": "ADMIN"}


def _client():
    app = FastAPI()
    app.include_router(admin_experience.router)
    app.dependency_overrides[require_system_admin_key] = _admin_identity
    return TestClient(app, raise_server_exceptions=False)


def test_get_admin_command_centre_returns_aggregate_payload(monkeypatch):
    async def fake_runtime():
        return {"status": "ok", "components": {"db": {"ok": True}}}

    async def fake_events():
        return {"total": 3, "problem_count": 0}

    async def fake_audit(**kwargs):
        return {"total": 2, "tenant_code": kwargs["tenant_code"]}

    async def fake_finance(**kwargs):
        return {"summary": {"ready_count": 1}, "tenant_code": kwargs["tenant_code"]}

    async def fake_providers():
        return [{"provider_key": "cash", "status": "READY"}]

    monkeypatch.setattr(admin_experience, "_runtime_health_payload", fake_runtime)
    monkeypatch.setattr(admin_experience, "get_enterprise_event_summary", fake_events)
    monkeypatch.setattr(admin_experience, "get_admin_audit_summary", fake_audit)
    monkeypatch.setattr(admin_experience, "get_outcome_money_map", fake_finance)
    monkeypatch.setattr(admin_experience, "list_provider_sla_metrics", fake_providers)

    response = _client().get(
        "/v1/experience/admin-command-centre",
        params={"tenant_code": "fnb"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert body["unavailableSections"] == []
    assert set(body["sections"]) == {
        "runtime",
        "events",
        "audit",
        "finance",
        "providers",
    }
    assert body["sections"]["finance"]["data"]["tenant_code"] == "FNB"
    assert body["sections"]["providers"]["data"][0]["provider_key"] == "cash"


def test_get_admin_command_centre_reports_partial_sections(monkeypatch):
    async def fake_runtime():
        return {"status": "ok"}

    async def failing_events():
        raise RuntimeError("event summary unavailable")

    async def fake_audit(**kwargs):
        return {"total": 0}

    async def fake_finance(**kwargs):
        return {"summary": {}}

    async def fake_providers():
        return []

    monkeypatch.setattr(admin_experience, "_runtime_health_payload", fake_runtime)
    monkeypatch.setattr(admin_experience, "get_enterprise_event_summary", failing_events)
    monkeypatch.setattr(admin_experience, "get_admin_audit_summary", fake_audit)
    monkeypatch.setattr(admin_experience, "get_outcome_money_map", fake_finance)
    monkeypatch.setattr(admin_experience, "list_provider_sla_metrics", fake_providers)

    response = _client().get(
        "/v1/experience/admin-command-centre",
        params={"tenant_code": "FNB"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["sections"]["events"]["status"] == "unavailable"
    assert body["sections"]["events"]["degraded"] is True
    assert body["sections"]["runtime"]["status"] == "ok"
    assert body["unavailableSections"] == ["events"]


def test_get_admin_command_centre_times_out_slow_sections(monkeypatch):
    async def fake_runtime():
        return {"status": "ok"}

    async def slow_events():
        await asyncio.sleep(0.2)
        return {"total": 1}

    async def fake_audit(**kwargs):
        return {"total": 0}

    async def fake_finance(**kwargs):
        return {"summary": {}}

    async def fake_providers():
        return []

    monkeypatch.setattr(admin_experience, "_runtime_health_payload", fake_runtime)
    monkeypatch.setattr(admin_experience, "get_enterprise_event_summary", slow_events)
    monkeypatch.setattr(admin_experience, "get_admin_audit_summary", fake_audit)
    monkeypatch.setattr(admin_experience, "get_outcome_money_map", fake_finance)
    monkeypatch.setattr(admin_experience, "list_provider_sla_metrics", fake_providers)

    response = _client().get(
        "/v1/experience/admin-command-centre",
        params={"tenant_code": "FNB", "section_timeout_seconds": 0.05},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["sections"]["events"]["status"] == "timeout"
    assert body["sections"]["events"]["degraded"] is True
    assert "timed out" in body["sections"]["events"]["error"]


def test_get_admin_command_centre_records_aggregate_metrics(monkeypatch):
    section_metrics = []
    request_metrics = []

    async def fake_runtime():
        return {"status": "ok"}

    async def fake_events():
        return {"total": 0}

    async def fake_audit(**kwargs):
        return {"total": 0}

    async def failing_finance(**kwargs):
        raise RuntimeError("finance unavailable")

    async def fake_providers():
        return []

    monkeypatch.setattr(admin_experience, "_runtime_health_payload", fake_runtime)
    monkeypatch.setattr(admin_experience, "get_enterprise_event_summary", fake_events)
    monkeypatch.setattr(admin_experience, "get_admin_audit_summary", fake_audit)
    monkeypatch.setattr(admin_experience, "get_outcome_money_map", failing_finance)
    monkeypatch.setattr(admin_experience, "list_provider_sla_metrics", fake_providers)
    monkeypatch.setattr(
        admin_experience,
        "bff_aggregate_section_observe",
        lambda **kwargs: section_metrics.append(kwargs),
    )
    monkeypatch.setattr(
        admin_experience,
        "bff_aggregate_request_inc",
        lambda **kwargs: request_metrics.append(kwargs),
    )

    response = _client().get(
        "/v1/experience/admin-command-centre",
        params={"tenant_code": "FNB"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "partial"
    assert request_metrics == [
        {"route": "admin_command_centre", "tenant": "FNB", "status": "partial"}
    ]

    statuses_by_section = {
        metric["section"]: metric["status"] for metric in section_metrics
    }
    assert statuses_by_section == {
        "runtime": "ok",
        "events": "ok",
        "audit": "ok",
        "finance": "unavailable",
        "providers": "ok",
    }
    assert all(metric["route"] == "admin_command_centre" for metric in section_metrics)
    assert all(metric["tenant"] == "FNB" for metric in section_metrics)
    assert all(metric["latency_seconds"] >= 0 for metric in section_metrics)
