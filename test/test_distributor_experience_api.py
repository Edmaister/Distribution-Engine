from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.distributor_experience as distributor_experience
from utils.security import require_admin_partner_or_distributor_key


def _client(identity: dict | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(distributor_experience.router)
    app.dependency_overrides[require_admin_partner_or_distributor_key] = lambda: identity or {
        "tenant_code": "FNB",
        "tenant": "FNB",
        "role": "DISTRIBUTOR",
        "distributor_code": "DIST-001",
    }
    return TestClient(app, raise_server_exceptions=False)


def _stub_sections(monkeypatch):
    async def fake_profile(**kwargs):
        return {"distributor_code": kwargs["distributor_code"]}

    async def fake_opportunities(**kwargs):
        return {"count": 1, "items": [{"route_status": "ROUTED"}]}

    async def fake_wallet(**kwargs):
        return {"count": 1, "items": [{"available_balance": "100.00"}]}

    async def fake_conversions(**kwargs):
        return {"count": 1, "completed_count": 0, "items": []}

    async def fake_performance(**kwargs):
        return {"accepted_count": 1, "total_commission_amount": "25.00"}

    async def fake_outcome_money(**kwargs):
        return {"summary": {"attention_count": 0}}

    async def fake_proof(**kwargs):
        return {"status": "ok", "proof": []}

    async def fake_channels(**kwargs):
        return {"readiness": [], "recommendations": []}

    monkeypatch.setattr(distributor_experience, "get_portal_distributor", fake_profile)
    monkeypatch.setattr(distributor_experience, "list_portal_offers", fake_opportunities)
    monkeypatch.setattr(distributor_experience, "list_portal_wallets", fake_wallet)
    monkeypatch.setattr(distributor_experience, "list_portal_conversions", fake_conversions)
    monkeypatch.setattr(distributor_experience, "get_portal_performance", fake_performance)
    monkeypatch.setattr(
        distributor_experience,
        "get_distributor_outcome_money_review",
        fake_outcome_money,
    )
    monkeypatch.setattr(
        distributor_experience,
        "get_distributor_insurance_journey_proof",
        fake_proof,
    )
    monkeypatch.setattr(distributor_experience, "_channel_guidance", fake_channels)


def test_distributor_experience_aggregates_portal_sections(monkeypatch):
    _stub_sections(monkeypatch)

    response = _client().get(
        "/v1/experience/distributor",
        params={"tenant_code": "fnb", "distributor_code": "dist-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert body["distributorCode"] == "DIST-001"
    assert body["unavailableSections"] == []
    assert set(body["sections"]) == {
        "profile",
        "opportunities",
        "wallet",
        "conversions",
        "performance",
        "outcomeMoney",
        "proof",
        "channels",
    }


def test_distributor_experience_enforces_distributor_scope(monkeypatch):
    _stub_sections(monkeypatch)

    response = _client(
        {
            "tenant_code": "FNB",
            "tenant": "FNB",
            "role": "DISTRIBUTOR",
            "distributor_code": "OTHER",
        }
    ).get(
        "/v1/experience/distributor",
        params={"tenant_code": "FNB", "distributor_code": "DIST-001"},
    )

    assert response.status_code == 403


def test_distributor_experience_marks_failed_section_partial(monkeypatch):
    _stub_sections(monkeypatch)

    async def broken_wallet(**kwargs):
        raise RuntimeError("wallet store unavailable")

    monkeypatch.setattr(distributor_experience, "list_portal_wallets", broken_wallet)

    response = _client().get(
        "/v1/experience/distributor",
        params={"tenant_code": "FNB", "distributor_code": "DIST-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["unavailableSections"] == ["wallet"]
    assert body["sections"]["wallet"]["status"] == "unavailable"
    assert body["sections"]["wallet"]["degraded"] is True


def test_distributor_experience_marks_timed_out_section(monkeypatch):
    _stub_sections(monkeypatch)

    async def slow_opportunities(**kwargs):
        await asyncio.sleep(0.1)
        return {"count": 0, "items": []}

    monkeypatch.setattr(
        distributor_experience,
        "list_portal_offers",
        slow_opportunities,
    )

    response = _client().get(
        "/v1/experience/distributor",
        params={
            "tenant_code": "FNB",
            "distributor_code": "DIST-001",
            "section_timeout_seconds": 0.05,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["unavailableSections"] == ["opportunities"]
    assert body["sections"]["opportunities"]["status"] == "timeout"


def test_distributor_experience_emits_bff_metrics(monkeypatch):
    _stub_sections(monkeypatch)
    requests: list[dict] = []
    sections: list[dict] = []

    async def broken_performance(**kwargs):
        raise RuntimeError("commission summary unavailable")

    monkeypatch.setattr(distributor_experience, "get_portal_performance", broken_performance)
    monkeypatch.setattr(
        distributor_experience,
        "bff_aggregate_request_inc",
        lambda **kwargs: requests.append(kwargs),
    )
    monkeypatch.setattr(
        distributor_experience,
        "bff_aggregate_section_observe",
        lambda **kwargs: sections.append(kwargs),
    )

    response = _client().get(
        "/v1/experience/distributor",
        params={"tenant_code": "FNB", "distributor_code": "DIST-001"},
    )

    assert response.status_code == 200
    assert requests == [
        {"route": "distributor", "tenant": "FNB", "status": "partial"}
    ]
    assert any(
        section["section"] == "performance" and section["status"] == "unavailable"
        for section in sections
    )
