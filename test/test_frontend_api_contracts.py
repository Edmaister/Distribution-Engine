from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import apps.api.routers.consumer_experience as consumer_experience
import apps.api.routers.admin_experience as admin_experience
import apps.api.routers.distributor_experience as distributor_experience
import apps.api.routers.sponsor_experience as sponsor_experience
from apps.api.routers import session
from utils.security import (
    require_admin_partner_or_consumer_key,
    require_admin_partner_or_distributor_key,
    require_admin_partner_or_producer_key,
    require_session_key,
    require_system_admin_key,
)


def _consumer_client() -> TestClient:
    app = FastAPI()
    app.include_router(consumer_experience.router)
    app.dependency_overrides[require_admin_partner_or_consumer_key] = lambda: {
        "tenant_code": "FNB",
        "tenant": "FNB",
        "role": "CONSUMER",
    }
    return TestClient(app, raise_server_exceptions=False)


def _session_client(identity: dict) -> TestClient:
    app = FastAPI()
    app.include_router(session.router)
    app.dependency_overrides[require_session_key] = lambda: identity
    return TestClient(app, raise_server_exceptions=False)


def _admin_experience_client() -> TestClient:
    app = FastAPI()
    app.include_router(admin_experience.router)
    app.dependency_overrides[require_system_admin_key] = lambda: {
        "tenant_code": "INTERNAL",
        "role": "ADMIN",
    }
    return TestClient(app, raise_server_exceptions=False)


def _distributor_experience_client() -> TestClient:
    app = FastAPI()
    app.include_router(distributor_experience.router)
    app.dependency_overrides[require_admin_partner_or_distributor_key] = lambda: {
        "tenant_code": "FNB",
        "tenant": "FNB",
        "role": "DISTRIBUTOR",
        "distributor_code": "DIST-001",
    }
    return TestClient(app, raise_server_exceptions=False)


def _sponsor_experience_client() -> TestClient:
    app = FastAPI()
    app.include_router(sponsor_experience.router)
    app.dependency_overrides[require_admin_partner_or_producer_key] = lambda: {
        "tenant_code": "FNB",
        "tenant": "FNB",
        "role": "PARTNER",
    }
    return TestClient(app, raise_server_exceptions=False)


def test_consumer_experience_contract_matches_frontend_payload(monkeypatch):
    async def fake_referrals(referrer_ucn, tenant_code):
        return [{"referral_track_id": "track-1", "tenant_code": tenant_code}]

    async def fake_rewards(referrer_ucn, tenant_code=None):
        return {"referrerUcn": referrer_ucn, "currency": "ZAR"}

    async def fake_missions(**kwargs):
        return {"core": [], "boost": [], "milestone": []}

    async def fake_leaderboard(code, referrer_ucn, tenant_code=None):
        return {"leaderboard_code": code, "rank_position": 1}

    async def fake_next_rank(code, referrer_ucn, tenant_code=None):
        return {"points_to_next_rank": 0}

    monkeypatch.setattr(
        consumer_experience.dashboard_router,
        "_get_referrals_for_referrer",
        fake_referrals,
    )
    monkeypatch.setattr(consumer_experience, "get_reward_summary_for_referrer", fake_rewards)
    monkeypatch.setattr(consumer_experience, "get_missions_for_referrer", fake_missions)
    monkeypatch.setattr(consumer_experience, "get_referrer_leaderboard_entry", fake_leaderboard)
    monkeypatch.setattr(consumer_experience, "get_next_rank_info", fake_next_rank)

    response = _consumer_client().get(
        "/v1/experience/consumer",
        params={
            "tenant_code": "FNB",
            "referrer_ucn": "900010",
            "leaderboard_code": "GLOBAL_OVERALL",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "status",
        "tenantCode",
        "referrerUcn",
        "referralTrackId",
        "leaderboardCode",
        "sections",
        "unavailableSections",
        "guardrail",
    }
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert body["referrerUcn"] == "900010"
    assert body["leaderboardCode"] == "GLOBAL_OVERALL"
    assert set(body["sections"]) == {"profile", "rewards", "missions", "leaderboard"}

    for section_name in ("profile", "rewards", "missions", "leaderboard"):
        assert set(body["sections"][section_name]) == {
            "status",
            "data",
            "error",
            "degraded",
        }
        assert body["sections"][section_name]["status"] == "ok"
        assert body["sections"][section_name]["degraded"] is False


def test_session_contract_matches_frontend_workspace_payload():
    response = _session_client(
        {
            "authenticated": True,
            "role": "CONSUMER",
            "tenant_code": "FNB",
            "tenant": "FNB",
            "auth_source": "api_key",
            "internal_secret": "must-not-leak",
        }
    ).get("/auth/session")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "session", "recommended_workspace", "workspaces"}
    assert body["status"] == "ok"
    assert body["session"] == {
        "authenticated": True,
        "role": "CONSUMER",
        "tenant_code": "FNB",
        "tenant": "FNB",
        "auth_source": "api_key",
    }

    recommended = body["recommended_workspace"]
    assert recommended["code"] == "consumer_journey"
    assert recommended["path"] == "/consumer"
    assert recommended["access"] == "allowed"
    assert recommended["scope"]["tenant_code"] == "FNB"

    workspace = body["workspaces"][0]
    assert set(workspace) == {
        "code",
        "label",
        "path",
        "summary",
        "access",
        "guidance",
        "scope",
    }


def test_admin_command_centre_contract_matches_frontend_payload(monkeypatch):
    async def fake_runtime():
        return {"status": "ok"}

    async def fake_events():
        return {"total": 0}

    async def fake_audit(**kwargs):
        return {"total": 0}

    async def fake_finance(**kwargs):
        return {"summary": {}}

    async def fake_providers():
        return []

    monkeypatch.setattr(admin_experience, "_runtime_health_payload", fake_runtime)
    monkeypatch.setattr(admin_experience, "get_enterprise_event_summary", fake_events)
    monkeypatch.setattr(admin_experience, "get_admin_audit_summary", fake_audit)
    monkeypatch.setattr(admin_experience, "get_outcome_money_map", fake_finance)
    monkeypatch.setattr(admin_experience, "list_provider_sla_metrics", fake_providers)

    response = _admin_experience_client().get(
        "/v1/experience/admin-command-centre",
        params={"tenant_code": "FNB"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "status",
        "tenantCode",
        "sections",
        "unavailableSections",
        "guardrail",
    }
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert set(body["sections"]) == {
        "runtime",
        "events",
        "audit",
        "finance",
        "providers",
    }

    for section_name in ("runtime", "events", "audit", "finance", "providers"):
        assert set(body["sections"][section_name]) == {
            "status",
            "data",
            "error",
            "degraded",
        }
        assert body["sections"][section_name]["status"] == "ok"
        assert body["sections"][section_name]["degraded"] is False


def test_distributor_experience_contract_matches_frontend_payload(monkeypatch):
    async def fake_profile(**kwargs):
        return {"distributor_code": kwargs["distributor_code"]}

    async def fake_opportunities(**kwargs):
        return {"count": 0, "items": []}

    async def fake_wallet(**kwargs):
        return {"count": 0, "items": []}

    async def fake_conversions(**kwargs):
        return {"count": 0, "items": []}

    async def fake_performance(**kwargs):
        return {"accepted_count": 0}

    async def fake_outcome_money(**kwargs):
        return {"summary": {}}

    async def fake_proof(**kwargs):
        return {"status": "ok"}

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

    response = _distributor_experience_client().get(
        "/v1/experience/distributor",
        params={"tenant_code": "FNB", "distributor_code": "DIST-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "status",
        "tenantCode",
        "distributorCode",
        "sections",
        "unavailableSections",
        "guardrail",
    }
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert body["distributorCode"] == "DIST-001"
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

    for section_name in (
        "profile",
        "opportunities",
        "wallet",
        "conversions",
        "performance",
        "outcomeMoney",
        "proof",
        "channels",
    ):
        assert set(body["sections"][section_name]) == {
            "status",
            "data",
            "error",
            "degraded",
        }
        assert body["sections"][section_name]["status"] == "ok"
        assert body["sections"][section_name]["degraded"] is False


def test_sponsor_experience_contract_matches_frontend_payload(monkeypatch):
    async def fake_billing(**kwargs):
        return {"invoice_count": 0}

    async def fake_invoices(**kwargs):
        return []

    async def fake_receipts(**kwargs):
        return []

    async def fake_wallet(**kwargs):
        return {"wallet": {}}

    async def fake_contracts(**kwargs):
        return []

    async def fake_forecast(**kwargs):
        return {"forecast": {}}

    async def fake_alerts(**kwargs):
        return {"count": 0, "items": []}

    async def fake_opportunities(**kwargs):
        return []

    async def fake_performance_overview(**kwargs):
        return {}

    async def fake_opportunity_performance(**kwargs):
        return []

    async def fake_conversions(**kwargs):
        return {"count": 0, "items": []}

    async def fake_outcome_money(**kwargs):
        return {"summary": {}}

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

    response = _sponsor_experience_client().get(
        "/v1/experience/sponsor",
        params={"tenant_code": "FNB", "sponsor_code": "INSURECO"},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "status",
        "tenantCode",
        "sponsorCode",
        "sections",
        "unavailableSections",
        "guardrail",
    }
    assert body["status"] == "ok"
    assert body["tenantCode"] == "FNB"
    assert body["sponsorCode"] == "INSURECO"
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

    for section_name in (
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
    ):
        assert set(body["sections"][section_name]) == {
            "status",
            "data",
            "error",
            "degraded",
        }
        assert body["sections"][section_name]["status"] == "ok"
        assert body["sections"][section_name]["degraded"] is False
