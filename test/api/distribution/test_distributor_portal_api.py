from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers.distribution import distributor_portal

PORTAL_HEADERS = {"x-api-key": "test-fnb-key"}
DISTRIBUTOR_HEADERS = {"x-api-key": "test-fnb-distributor-insurance-advocate-key"}


pytestmark = pytest.mark.asyncio


def distributor_payload(distributor_id: str, **overrides):
    payload = {
        "distributor_id": distributor_id,
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "distributor_name": "Agency One",
        "distributor_type": "AGENCY",
        "status": "ACTIVE",
        "contact_email": "agency@example.com",
        "contact_phone": "+27110000000",
        "channels": ["FIELD"],
        "segments": ["MASS_MARKET"],
        "regions": ["ZA-GP"],
        "capabilities": {"languages": ["en"]},
        "eligibility": {"kyb_status": "APPROVED"},
        "operating_limits": {"daily_leads": 50},
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
        "status_changed_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


async def test_distributor_can_read_outcome_money_review(monkeypatch):
    async def fake_get_distributor_outcome_money_review(**kwargs):
        assert kwargs == {
            "tenant_code": "FNB",
            "distributor_code": "DIST-INSURANCE-ADVOCATE",
            "limit": 25,
        }
        return {
            "surface": "Distributor - Demand",
            "summary": {"attention_count": 1},
            "items": [],
        }

    monkeypatch.setattr(
        distributor_portal,
        "get_distributor_outcome_money_review",
        fake_get_distributor_outcome_money_review,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/distribution/portal/outcome-money-review?tenant_code=FNB&distributor_code=DIST-INSURANCE-ADVOCATE&limit=25",
            headers=DISTRIBUTOR_HEADERS,
        )

    assert response.status_code == 200
    assert response.json()["review"]["surface"] == "Distributor - Demand"
    assert response.json()["review"]["summary"]["attention_count"] == 1


async def test_distributor_can_read_channel_recommendations(monkeypatch):
    def fake_recommend_channels(**kwargs):
        assert kwargs == {
            "event_type": "ROUTE_ASSIGNED",
            "audience": "DISTRIBUTOR",
            "distributor_channels": ["WHATSAPP"],
        }
        return {
            "status": "READY",
            "top_channel": {"channel_code": "WHATSAPP"},
            "items": [],
        }

    monkeypatch.setattr(
        distributor_portal, "recommend_channels", fake_recommend_channels
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/distribution/portal/channel-recommendations?tenant_code=FNB&distributor_code=DIST-INSURANCE-ADVOCATE&event_type=ROUTE_ASSIGNED&audience=DISTRIBUTOR&distributor_channels=WHATSAPP",
            headers=DISTRIBUTOR_HEADERS,
        )

    assert response.status_code == 200
    assert (
        response.json()["recommendations"]["top_channel"]["channel_code"] == "WHATSAPP"
    )


async def test_distributor_can_read_channel_readiness(monkeypatch):
    def fake_get_channel_readiness():
        return {
            "status": "ATTENTION",
            "summary": {"ready_count": 1, "count": 3},
            "items": [],
        }

    monkeypatch.setattr(
        distributor_portal, "get_channel_readiness", fake_get_channel_readiness
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/distribution/portal/channel-readiness?tenant_code=FNB&distributor_code=DIST-INSURANCE-ADVOCATE",
            headers=DISTRIBUTOR_HEADERS,
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == "Distributor - Demand"
    assert payload["tenant_code"] == "FNB"
    assert payload["distributor_code"] == "DIST-INSURANCE-ADVOCATE"
    assert payload["readiness"]["summary"]["ready_count"] == 1


def route_payload(route_id: str, opportunity_id: str, distributor_id: str, **overrides):
    payload = {
        "route_id": route_id,
        "tenant_code": "FNB",
        "opportunity_id": opportunity_id,
        "distributor_id": distributor_id,
        "route_status": "ROUTED",
        "route_score": Decimal("100.00"),
        "route_reasons": ["segment: matched MASS_MARKET"],
        "routed_at": "2026-06-12T10:00:00",
        "expires_at": None,
        "accepted_at": None,
        "declined_at": None,
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


def offer_payload(route_id: str, opportunity_id: str, distributor_id: str, **overrides):
    payload = {
        **route_payload(route_id, opportunity_id, distributor_id),
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "opportunity_code": "BOXER_HOME_LOANS",
        "title": "Boxer Home Loans",
        "description": "Funded acquisition opportunity",
        "product_code": "HOME_LOAN",
        "product_name": "Home Loan",
        "estimated_reward_amount": Decimal("100.00"),
        "estimated_commission_amount": Decimal("50.00"),
        "starts_at": "2026-06-12T10:00:00",
        "ends_at": "2026-12-31T23:59:59",
        "referral_link_count": 0,
        "latest_referral_track_id": None,
        "has_referral_link": False,
    }
    payload.update(overrides)
    return payload


def wallet_payload(wallet_id: str, distributor_id: str, **overrides):
    payload = {
        "wallet_id": wallet_id,
        "distributor_id": distributor_id,
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "currency": "ZAR",
        "current_balance": Decimal("100.00"),
        "available_balance": Decimal("75.00"),
        "held_balance": Decimal("25.00"),
        "paid_out_balance": Decimal("0.00"),
        "reversed_balance": Decimal("0.00"),
        "status": "ACTIVE",
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


def ledger_payload(ledger_id: str, wallet_id: str, distributor_id: str, **overrides):
    payload = {
        "ledger_id": ledger_id,
        "wallet_id": wallet_id,
        "distributor_id": distributor_id,
        "tenant_code": "FNB",
        "transaction_type": "CREDIT",
        "amount": Decimal("100.00"),
        "balance_before": Decimal("0.00"),
        "balance_after": Decimal("100.00"),
        "correlation_id": "commission-1",
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


def conversion_payload(referral_track_id: str, **overrides):
    payload = {
        "referral_track_id": referral_track_id,
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "product": "BANKING",
        "sub_product": "TRANSACTIONAL",
        "status": "FUNDED",
        "display_status": "Almost there",
        "progress_percent": 80,
        "progress_band": "ACTIVE",
        "next_milestone": "Salary switch or debit order switch",
        "is_complete": False,
        "completed_at": None,
        "validated_at": "2026-06-12T10:00:00",
        "ucn_captured_at": "2026-06-12T10:05:00",
        "account_opened_at": "2026-06-12T10:10:00",
        "account_activated_at": "2026-06-12T10:20:00",
        "funded_at": "2026-06-12T10:30:00",
        "debit_order_switched_at": None,
        "salary_switched_at": None,
        "first_transaction_completed_at": None,
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:30:00",
        "distributor_safe_status": {
            "status": "IN_PROGRESS",
            "label": "In progress",
            "summary": "Your outcome status is in progress.",
            "what_happened": "Outcome evidence was received.",
            "what_happens_next": "No action is required.",
            "action_required": False,
            "action_category": "NONE",
            "terminal": False,
            "source_families": ["outcome"],
            "source_confidence": "MEDIUM",
            "missing_evidence": [],
            "redactions": [
                "private_identifier",
                "provider_payload",
                "raw_status",
            ],
        },
    }
    payload.update(overrides)
    return payload


def route_referral_link_payload(
    route_id: str,
    referral_track_id: str,
    distributor_id: str,
    opportunity_id: str,
    **overrides,
):
    payload = {
        "route_id": route_id,
        "referral_track_id": referral_track_id,
        "tenant_code": "FNB",
        "distributor_id": distributor_id,
        "distributor_code": "AGENCY_001",
        "opportunity_id": opportunity_id,
        "link_status": "ACTIVE",
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


async def test_get_distributor_portal_profile(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    calls = {}

    async def fake_get_portal_distributor(**kwargs):
        calls.update(kwargs)
        return distributor_payload(distributor_id)

    monkeypatch.setattr(
        distributor_portal,
        "get_portal_distributor",
        fake_get_portal_distributor,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/profile",
            params={"tenant_code": "FNB", "distributor_code": "AGENCY_001"},
        )

    assert response.status_code == 200
    assert response.json()["distributor_id"] == distributor_id
    assert calls == {"tenant_code": "FNB", "distributor_code": "AGENCY_001"}


async def test_list_distributor_portal_offers(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    opportunity_id = str(uuid4())
    route_id = str(uuid4())
    calls = {}

    async def fake_list_portal_offers(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "distributor_id": distributor_id,
            "distributor_code": "AGENCY_001",
            "count": 1,
            "items": [offer_payload(route_id, opportunity_id, distributor_id)],
        }

    monkeypatch.setattr(
        distributor_portal,
        "list_portal_offers",
        fake_list_portal_offers,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/offers",
            params={
                "tenant_code": "FNB",
                "distributor_code": "AGENCY_001",
                "route_status": "ROUTED",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["title"] == "Boxer Home Loans"
    assert body["items"][0]["has_referral_link"] is False
    assert body["items"][0]["referral_link_count"] == 0
    assert calls == {
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "route_status": "ROUTED",
        "limit": 25,
    }


@pytest.mark.parametrize(
    ("endpoint", "service_name", "status_value"),
    [
        ("accept", "accept_portal_offer", "ACCEPTED"),
        ("decline", "decline_portal_offer", "DECLINED"),
    ],
)
async def test_distributor_portal_offer_actions(
    monkeypatch,
    endpoint,
    service_name,
    status_value,
):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    opportunity_id = str(uuid4())
    route_id = str(uuid4())
    calls = {}

    async def fake_offer_action(**kwargs):
        calls.update(kwargs)
        return route_payload(
            route_id,
            opportunity_id,
            distributor_id,
            route_status=status_value,
        )

    monkeypatch.setattr(distributor_portal, service_name, fake_offer_action)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.post(
            f"/distribution/portal/offers/{route_id}/{endpoint}",
            params={"tenant_code": "FNB", "distributor_code": "AGENCY_001"},
        )

    assert response.status_code == 200
    assert response.json()["route_status"] == status_value
    assert calls == {
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "route_id": route_id,
    }


async def test_distributor_portal_offer_action_rejects_decided_route(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    route_id = str(uuid4())

    async def fake_accept_portal_offer(**kwargs):
        raise distributor_portal.DistributorPortalError(
            "Only ROUTED offers can be accepted or declined"
        )

    monkeypatch.setattr(
        distributor_portal,
        "accept_portal_offer",
        fake_accept_portal_offer,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.post(
            f"/distribution/portal/offers/{route_id}/accept",
            params={"tenant_code": "FNB", "distributor_code": "AGENCY_001"},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only ROUTED offers can be accepted or declined"
    }


async def test_distributor_portal_link_offer_referral(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    opportunity_id = str(uuid4())
    route_id = str(uuid4())
    referral_track_id = str(uuid4())
    calls = {}

    async def fake_link_portal_referral_to_route(**kwargs):
        calls.update(kwargs)
        return route_referral_link_payload(
            route_id,
            referral_track_id,
            distributor_id,
            opportunity_id,
            metadata=kwargs["metadata"],
        )

    monkeypatch.setattr(
        distributor_portal,
        "link_portal_referral_to_route",
        fake_link_portal_referral_to_route,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.post(
            f"/distribution/portal/offers/{route_id}/referrals",
            params={"tenant_code": "FNB", "distributor_code": "AGENCY_001"},
            json={
                "referral_track_id": referral_track_id,
                "metadata": {"source": "distributor_portal"},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["route_id"] == route_id
    assert body["referral_track_id"] == referral_track_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "route_id": route_id,
        "referral_track_id": referral_track_id,
        "metadata": {"source": "distributor_portal"},
    }


async def test_distributor_portal_link_offer_referral_blocks_unaccepted_route(
    monkeypatch,
):
    from apps.api.routers.distribution import distributor_portal

    route_id = str(uuid4())
    referral_track_id = str(uuid4())

    async def fake_link_portal_referral_to_route(**kwargs):
        raise distributor_portal.DistributorPortalError(
            "Only accepted routes can be linked to customer conversions"
        )

    monkeypatch.setattr(
        distributor_portal,
        "link_portal_referral_to_route",
        fake_link_portal_referral_to_route,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.post(
            f"/distribution/portal/offers/{route_id}/referrals",
            params={"tenant_code": "FNB", "distributor_code": "AGENCY_001"},
            json={"referral_track_id": referral_track_id},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only accepted routes can be linked to customer conversions"
    }


async def test_list_distributor_portal_wallets(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    wallet_id = str(uuid4())
    calls = {}

    async def fake_list_portal_wallets(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "distributor_id": distributor_id,
            "distributor_code": "AGENCY_001",
            "count": 1,
            "items": [wallet_payload(wallet_id, distributor_id)],
        }

    monkeypatch.setattr(
        distributor_portal,
        "list_portal_wallets",
        fake_list_portal_wallets,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/wallets",
            params={
                "tenant_code": "FNB",
                "distributor_code": "AGENCY_001",
                "limit": 10,
            },
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["wallet_id"] == wallet_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "limit": 10,
    }


async def test_list_distributor_portal_wallet_ledger(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    wallet_id = str(uuid4())
    ledger_id = str(uuid4())
    calls = {}

    async def fake_list_portal_wallet_ledger(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "distributor_id": distributor_id,
            "distributor_code": "AGENCY_001",
            "wallet_id": wallet_id,
            "count": 1,
            "items": [ledger_payload(ledger_id, wallet_id, distributor_id)],
        }

    monkeypatch.setattr(
        distributor_portal,
        "list_portal_wallet_ledger",
        fake_list_portal_wallet_ledger,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            f"/distribution/portal/wallets/{wallet_id}/ledger",
            params={
                "tenant_code": "FNB",
                "distributor_code": "AGENCY_001",
                "limit": 10,
            },
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["ledger_id"] == ledger_id
    assert calls == {
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "wallet_id": wallet_id,
        "limit": 10,
    }


async def test_list_distributor_portal_conversions(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    referral_track_id = str(uuid4())
    calls = {}

    async def fake_list_portal_conversions(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "distributor_id": distributor_id,
            "distributor_code": "AGENCY_001",
            "count": 1,
            "completed_count": 0,
            "completion_rate": Decimal("0.0000"),
            "attributed_count": 0,
            "unlinked_count": 1,
            "attribution_rate": Decimal("0.0000"),
            "items": [conversion_payload(referral_track_id)],
        }

    monkeypatch.setattr(
        distributor_portal,
        "list_portal_conversions",
        fake_list_portal_conversions,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/conversions",
            params={
                "tenant_code": "FNB",
                "distributor_code": "AGENCY_001",
                "limit": 10,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["completed_count"] == 0
    assert body["completion_rate"] == "0.0000"
    assert body["attributed_count"] == 0
    assert body["unlinked_count"] == 1
    assert body["attribution_rate"] == "0.0000"
    assert body["items"][0]["referral_track_id"] == referral_track_id
    assert body["items"][0]["distributor_safe_status"]["status"] == "IN_PROGRESS"
    assert body["items"][0]["distributor_safe_status"]["action_category"] == "NONE"
    assert "tenant_code" not in str(body["items"][0]["distributor_safe_status"])
    assert "ucn" not in str(body["items"][0]["distributor_safe_status"]).lower()
    assert calls == {
        "tenant_code": "FNB",
        "distributor_code": "AGENCY_001",
        "limit": 10,
    }


async def test_get_distributor_portal_performance(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    distributor_id = str(uuid4())
    calls = {}

    async def fake_get_portal_performance(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "distributor_id": distributor_id,
            "distributor_code": "AGENCY_001",
            "routed_count": 10,
            "accepted_count": 4,
            "declined_count": 2,
            "acceptance_rate": Decimal("0.4000"),
            "conversion_count": 5,
            "completed_conversion_count": 2,
            "conversion_completion_rate": Decimal("0.4000"),
            "commission_event_count": 3,
            "total_commission_amount": Decimal("150.00"),
            "wallet_current_balance": Decimal("100.00"),
            "wallet_available_balance": Decimal("75.00"),
            "wallet_held_balance": Decimal("25.00"),
            "wallet_paid_out_balance": Decimal("0.00"),
            "wallet_reversed_balance": Decimal("0.00"),
        }

    monkeypatch.setattr(
        distributor_portal,
        "get_portal_performance",
        fake_get_portal_performance,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/performance",
            params={"tenant_code": "FNB", "distributor_code": "AGENCY_001"},
        )

    assert response.status_code == 200
    assert response.json()["acceptance_rate"] == "0.4000"
    assert response.json()["conversion_count"] == 5
    assert response.json()["completed_conversion_count"] == 2
    assert response.json()["conversion_completion_rate"] == "0.4000"
    assert calls == {"tenant_code": "FNB", "distributor_code": "AGENCY_001"}


async def test_get_distributor_portal_insurance_proof(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    async def fake_get_distributor_insurance_journey_proof(**kwargs):
        return {
            "scope": "distributor",
            "surface": "Distributor - Demand",
            "tenant_code": kwargs["tenant_code"],
            "distributor_code": kwargs["distributor_code"],
            "status": "READY",
            "commission_amount": "75.00",
            "steps": [{"surface": "Distributor - Demand", "status": "READY"}],
        }

    monkeypatch.setattr(
        distributor_portal,
        "get_distributor_insurance_journey_proof",
        fake_get_distributor_insurance_journey_proof,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/proof/insurance",
            params={
                "tenant_code": "FNB",
                "distributor_code": "DIST-INSURANCE-ADVOCATE",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "distributor"
    assert body["surface"] == "Distributor - Demand"
    assert body["tenant_code"] == "FNB"
    assert body["distributor_code"] == "DIST-INSURANCE-ADVOCATE"
    assert body["steps"][0]["surface"] == "Distributor - Demand"


async def test_get_distributor_portal_insurance_proof_rejects_other_distributor_key(
    monkeypatch,
):
    from apps.api.routers.distribution import distributor_portal

    async def fake_get_distributor_insurance_journey_proof(**kwargs):
        return {"status": "READY"}

    monkeypatch.setattr(
        distributor_portal,
        "get_distributor_insurance_journey_proof",
        fake_get_distributor_insurance_journey_proof,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTOR_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/proof/insurance",
            params={"tenant_code": "FNB", "distributor_code": "OTHER"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "API key is not authorised for this distributor"


async def test_distributor_portal_missing_distributor_returns_404(monkeypatch):
    from apps.api.routers.distribution import distributor_portal

    async def fake_get_portal_distributor(**kwargs):
        raise distributor_portal.DistributorPortalNotFound("Distributor not found")

    monkeypatch.setattr(
        distributor_portal,
        "get_portal_distributor",
        fake_get_portal_distributor,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PORTAL_HEADERS
    ) as client:
        response = await client.get(
            "/distribution/portal/profile",
            params={"tenant_code": "FNB", "distributor_code": "MISSING"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Distributor not found"}
