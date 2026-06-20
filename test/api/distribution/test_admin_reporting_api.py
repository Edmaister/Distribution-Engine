from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


async def test_get_marketplace_overview(monkeypatch):
    from apps.api.routers.distribution import admin_reporting

    calls = {}

    async def fake_get_marketplace_overview(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "campaign_code": "BOXER_ACQ",
            "distributors": {"total_count": 10, "active_count": 8},
            "opportunities": {"total_count": 4, "published_count": 3},
            "routes": {
                "total_count": 20,
                "accepted_count": 5,
                "acceptance_rate": Decimal("0.2500"),
            },
            "commissions": {"event_count": 3, "total_commission_amount": Decimal("150.00")},
            "conversions": {
                "linked_count": 4,
                "completed_count": 2,
                "completion_rate": Decimal("0.5000"),
                "total_referral_count": 5,
                "attributed_count": 4,
                "unlinked_count": 1,
                "attribution_rate": Decimal("0.8000"),
            },
            "wallets": {"wallet_count": 2, "current_balance": Decimal("100.00")},
            "governance": {"open_dispute_count": 1},
        }

    monkeypatch.setattr(
        admin_reporting,
        "get_marketplace_overview",
        fake_get_marketplace_overview,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/reporting/overview",
            params={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "campaign_code": "BOXER_ACQ",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["routes"]["acceptance_rate"] == "0.2500"
    assert body["conversions"]["linked_count"] == 4
    assert body["conversions"]["completed_count"] == 2
    assert body["conversions"]["completion_rate"] == "0.5000"
    assert body["conversions"]["unlinked_count"] == 1
    assert body["conversions"]["attribution_rate"] == "0.8000"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
    }


async def test_list_opportunity_performance(monkeypatch):
    from apps.api.routers.distribution import admin_reporting

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_list_opportunity_performance(**kwargs):
        calls.update(kwargs)
        return [
            {
                "opportunity_id": opportunity_id,
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "campaign_code": "BOXER_ACQ",
                "opportunity_code": "BOXER_HOME_LOANS",
                "title": "Boxer Home Loans",
                "opportunity_status": "PUBLISHED",
                "total_budget": Decimal("100000.00"),
                "remaining_budget": Decimal("90000.00"),
                "routed_count": 10,
                "accepted_count": 4,
                "declined_count": 2,
                "average_route_score": Decimal("87.50"),
                "conversion_count": 2,
                "completed_conversion_count": 1,
                "conversion_completion_rate": Decimal("0.5000"),
                "dispute_count": 1,
            }
        ]

    monkeypatch.setattr(
        admin_reporting,
        "list_opportunity_performance",
        fake_list_opportunity_performance,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/reporting/opportunities",
            params={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "campaign_code": "BOXER_ACQ",
                "opportunity_status": "PUBLISHED",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["opportunity_id"] == opportunity_id
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "opportunity_status": "PUBLISHED",
        "limit": 25,
    }


async def test_list_distributor_performance(monkeypatch):
    from apps.api.routers.distribution import admin_reporting

    distributor_id = str(uuid4())
    calls = {}

    async def fake_list_distributor_performance(**kwargs):
        calls.update(kwargs)
        return [
            {
                "distributor_id": distributor_id,
                "tenant_code": "FNB",
                "distributor_code": "AGENCY_001",
                "distributor_name": "Agency One",
                "distributor_type": "AGENCY",
                "status": "ACTIVE",
                "routed_count": 10,
                "accepted_count": 4,
                "declined_count": 2,
                "conversion_count": 3,
                "completed_conversion_count": 1,
                "conversion_completion_rate": Decimal("0.3333"),
                "commission_event_count": 3,
                "total_commission_amount": Decimal("150.00"),
                "wallet_current_balance": Decimal("100.00"),
                "wallet_available_balance": Decimal("75.00"),
                "dispute_count": 1,
                "open_compliance_review_count": 0,
            }
        ]

    monkeypatch.setattr(
        admin_reporting,
        "list_distributor_performance",
        fake_list_distributor_performance,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/reporting/distributors",
            params={
                "tenant_code": "FNB",
                "distributor_type": "AGENCY",
                "status": "ACTIVE",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()[0]["distributor_id"] == distributor_id
    assert response.json()[0]["conversion_count"] == 3
    assert response.json()[0]["completed_conversion_count"] == 1
    assert response.json()[0]["conversion_completion_rate"] == "0.3333"
    assert calls == {
        "tenant_code": "FNB",
        "distributor_type": "AGENCY",
        "status": "ACTIVE",
        "limit": 25,
    }


async def test_list_attribution_exceptions(monkeypatch):
    from apps.api.routers.distribution import admin_reporting

    referral_track_id = str(uuid4())
    calls = {}

    async def fake_list_attribution_exceptions(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "count": 1,
            "completed_count": 0,
            "items": [
                {
                    "referral_track_id": referral_track_id,
                    "tenant_code": "FNB",
                    "distributor_code": "AGENCY_001",
                    "product": "HOME_LOAN",
                    "sub_product": "SWITCH",
                    "status": "ACCOUNT_OPENED",
                    "display_status": "Account opened",
                    "progress_percent": 50,
                    "progress_band": "IN_PROGRESS",
                    "next_milestone": "Activation",
                    "is_complete": False,
                }
            ],
        }

    monkeypatch.setattr(
        admin_reporting,
        "list_attribution_exceptions",
        fake_list_attribution_exceptions,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/reporting/attribution-exceptions",
            params={"tenant_code": "FNB", "limit": 10},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["referral_track_id"] == referral_track_id
    assert body["items"][0]["next_milestone"] == "Activation"
    assert calls == {"tenant_code": "FNB", "limit": 10}


async def test_get_governance_report(monkeypatch):
    from apps.api.routers.distribution import admin_reporting

    calls = {}

    async def fake_get_governance_report(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "compliance_reviews": [{"status": "OPEN", "count": 2}],
            "disputes": [{"status": "RESOLVED", "count": 3}],
            "governance_actions": [{"action_type": "SUSPEND", "count": 1}],
        }

    monkeypatch.setattr(
        admin_reporting,
        "get_governance_report",
        fake_get_governance_report,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/reporting/governance",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200
    assert response.json()["governance_actions"][0]["action_type"] == "SUSPEND"
    assert calls == {"tenant_code": "FNB"}
