from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.sponsor_experience as sponsor_experience
from utils.security import require_admin_partner_or_producer_key


def _client(identity: dict | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(sponsor_experience.router)
    app.dependency_overrides[require_admin_partner_or_producer_key] = lambda: identity or {
        "tenant_code": "FNB",
        "tenant": "FNB",
        "role": "PARTNER",
    }
    return TestClient(app, raise_server_exceptions=False)


def _stub_sections(monkeypatch):
    async def fake_billing(**kwargs):
        return {"sponsor_code": kwargs["sponsor_code"], "invoice_count": 1}

    async def fake_invoices(**kwargs):
        return [{"invoice_id": "inv-1"}]

    async def fake_receipts(**kwargs):
        return [{"receipt_id": "rec-1"}]

    async def fake_wallet(**kwargs):
        return {"wallet": {"available_balance": "100.00"}}

    async def fake_contracts(**kwargs):
        return [{"contract_id": "contract-1"}]

    async def fake_forecast(**kwargs):
        return {"forecast": {"status": "HEALTHY"}}

    async def fake_alerts(**kwargs):
        return {"count": 0, "items": []}

    async def fake_opportunities(**kwargs):
        return [{"opportunity_id": "opp-1"}]

    async def fake_performance_overview(**kwargs):
        return {"opportunities": {"published_count": 1}}

    async def fake_opportunity_performance(**kwargs):
        return [{"opportunity_id": "opp-1", "conversion_count": 1}]

    async def fake_conversions(**kwargs):
        return {"count": 1, "items": [{"referral_track_id": "ref-1"}]}

    async def fake_outcome_money(**kwargs):
        return {"summary": {"attention_count": 0}}

    async def fake_proof(**kwargs):
        return {"status": "ok"}

    async def fake_channels(**kwargs):
        return {"readiness": {}, "recommendations": {}}

    monkeypatch.setattr(sponsor_experience, "get_sponsor_billing_dashboard", fake_billing)
    monkeypatch.setattr(sponsor_experience, "list_sponsor_invoices", fake_invoices)
    monkeypatch.setattr(
        sponsor_experience,
        "list_sponsor_payment_receipts",
        fake_receipts,
    )
    monkeypatch.setattr(sponsor_experience, "_wallet_payload", fake_wallet)
    monkeypatch.setattr(sponsor_experience, "list_funding_contracts", fake_contracts)
    monkeypatch.setattr(sponsor_experience, "_forecast_payload", fake_forecast)
    monkeypatch.setattr(sponsor_experience, "_alerts_payload", fake_alerts)
    monkeypatch.setattr(sponsor_experience, "list_opportunities", fake_opportunities)
    monkeypatch.setattr(sponsor_experience, "get_marketplace_overview", fake_performance_overview)
    monkeypatch.setattr(sponsor_experience, "list_opportunity_performance", fake_opportunity_performance)
    monkeypatch.setattr(sponsor_experience, "list_producer_conversion_journeys", fake_conversions)
    monkeypatch.setattr(sponsor_experience, "get_producer_outcome_money_review", fake_outcome_money)
    monkeypatch.setattr(sponsor_experience, "get_producer_insurance_journey_proof", fake_proof)
    monkeypatch.setattr(sponsor_experience, "_channel_guidance", fake_channels)


def test_sponsor_experience_aggregates_portal_sections(monkeypatch):
    _stub_sections(monkeypatch)

    response = _client().get(
        "/v1/experience/sponsor",
        params={"tenant_code": "fnb", "sponsor_code": "insureco"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert body["sponsorCode"] == "INSURECO"
    assert body["unavailableSections"] == []
    assert set(body["sections"]) == {
        "billing",
        "invoices",
        "receipts",
        "wallet",
        "contracts",
        "forecast",
        "alerts",
        "opportunities",
        "performanceOverview",
        "opportunityPerformance",
        "conversions",
        "outcomeMoney",
        "proof",
        "channels",
    }


def test_sponsor_experience_enforces_tenant_scope(monkeypatch):
    _stub_sections(monkeypatch)

    response = _client(
        {
            "tenant_code": "OTHER",
            "tenant": "OTHER",
            "role": "PARTNER",
        }
    ).get(
        "/v1/experience/sponsor",
        params={"tenant_code": "FNB", "sponsor_code": "INSURECO"},
    )

    assert response.status_code == 403


def test_sponsor_experience_marks_failed_section_partial(monkeypatch):
    _stub_sections(monkeypatch)

    async def broken_forecast(**kwargs):
        raise RuntimeError("forecast unavailable")

    monkeypatch.setattr(sponsor_experience, "_forecast_payload", broken_forecast)

    response = _client().get(
        "/v1/experience/sponsor",
        params={"tenant_code": "FNB", "sponsor_code": "INSURECO"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["unavailableSections"] == ["forecast"]
    assert body["sections"]["forecast"]["status"] == "unavailable"
    assert body["sections"]["forecast"]["degraded"] is True


def test_sponsor_experience_marks_timed_out_section(monkeypatch):
    _stub_sections(monkeypatch)

    async def slow_billing(**kwargs):
        await asyncio.sleep(0.1)
        return {"invoice_count": 0}

    monkeypatch.setattr(sponsor_experience, "get_sponsor_billing_dashboard", slow_billing)

    response = _client().get(
        "/v1/experience/sponsor",
        params={
            "tenant_code": "FNB",
            "sponsor_code": "INSURECO",
            "section_timeout_seconds": 0.05,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["unavailableSections"] == ["billing"]
    assert body["sections"]["billing"]["status"] == "timeout"


def test_sponsor_experience_emits_bff_metrics(monkeypatch):
    _stub_sections(monkeypatch)
    requests: list[dict] = []
    sections: list[dict] = []

    async def broken_wallet(**kwargs):
        raise RuntimeError("wallet unavailable")

    monkeypatch.setattr(sponsor_experience, "_wallet_payload", broken_wallet)
    monkeypatch.setattr(
        sponsor_experience,
        "bff_aggregate_request_inc",
        lambda **kwargs: requests.append(kwargs),
    )
    monkeypatch.setattr(
        sponsor_experience,
        "bff_aggregate_section_observe",
        lambda **kwargs: sections.append(kwargs),
    )

    response = _client().get(
        "/v1/experience/sponsor",
        params={"tenant_code": "FNB", "sponsor_code": "INSURECO"},
    )

    assert response.status_code == 200
    assert requests == [{"route": "sponsor", "tenant": "FNB", "status": "partial"}]
    assert any(
        section["section"] == "wallet" and section["status"] == "unavailable"
        for section in sections
    )
