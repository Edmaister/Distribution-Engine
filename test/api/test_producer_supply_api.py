from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import producer_supply


PARTNER_HEADERS = {"x-api-key": "test-fnb-key"}
PRODUCER_HEADERS = {"x-api-key": "test-fnb-producer-insureco-key"}


pytestmark = pytest.mark.asyncio


def opportunity_payload(opportunity_id: str, *, status: str = "DRAFT") -> dict:
    return {
        "opportunity_id": opportunity_id,
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "SWITCH_SALARY",
        "funding_contract_id": None,
        "opportunity_code": "SWITCH_SALARY-OPP",
        "title": "Switch your salary",
        "description": "Acquire salary switchers",
        "product_code": "TRANSACTIONAL_ACCOUNT",
        "product_name": "Transactional account",
        "opportunity_status": status,
        "target_segments": ["BANKING"],
        "target_regions": ["ZA"],
        "target_channels": ["WHATSAPP"],
        "distributor_types": ["BROKER"],
        "commission_rule_id": None,
        "estimated_reward_amount": "100.00",
        "estimated_commission_amount": "25.00",
        "total_budget": "10000.00",
        "remaining_budget": "10000.00",
        "max_allocations": 100,
        "remaining_allocations": 100,
        "starts_at": None,
        "ends_at": None,
        "published_at": None,
        "closed_at": None,
        "metadata": {"source": "test"},
        "created_at": "2026-06-16T10:00:00",
        "updated_at": "2026-06-16T10:00:00",
    }


def producer_conversion_payload(
    *,
    referral_track_id: str,
    opportunity_id: str,
    route_id: str,
    distributor_id: str,
) -> dict:
    return {
        "referral_track_id": referral_track_id,
        "tenant_code": "FNB",
        "producer_code": "BOXER",
        "campaign_code": "SWITCH_SALARY",
        "opportunity_id": opportunity_id,
        "opportunity_code": "SWITCH_SALARY-OPP",
        "opportunity_title": "Switch your salary",
        "route_id": route_id,
        "distributor_id": distributor_id,
        "distributor_code": "DIST001",
        "distributor_name": "Distributor One",
        "distributor_type": "BROKER",
        "product": "TRANSACTIONAL_ACCOUNT",
        "sub_product": "SALARY_SWITCH",
        "status": "ACCOUNT_OPENED",
        "display_status": "Account opened",
        "progress_percent": 60,
        "progress_band": "IN_PROGRESS",
        "next_milestone": "Activate account",
        "is_complete": False,
        "completed_at": None,
        "validated_at": "2026-06-16T10:00:00",
        "ucn_captured_at": "2026-06-16T10:00:00",
        "account_opened_at": "2026-06-16T10:05:00",
        "account_activated_at": None,
        "funded_at": None,
        "debit_order_switched_at": None,
        "salary_switched_at": None,
        "first_transaction_completed_at": None,
        "created_at": "2026-06-16T10:00:00",
        "updated_at": "2026-06-16T10:05:00",
    }


async def test_producer_can_read_outcome_money_review(monkeypatch):
    async def fake_get_producer_outcome_money_review(**kwargs):
        assert kwargs == {
            "tenant_code": "FNB",
            "producer_code": "INSURECO",
            "limit": 25,
        }
        return {
            "surface": "Producer - Supply",
            "summary": {"attention_count": 1},
            "items": [],
        }

    monkeypatch.setattr(
        producer_supply,
        "get_producer_outcome_money_review",
        fake_get_producer_outcome_money_review,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/INSURECO/supply/outcome-money-review?limit=25",
            headers=PRODUCER_HEADERS,
        )

    assert response.status_code == 200
    assert response.json()["review"]["surface"] == "Producer - Supply"
    assert response.json()["review"]["summary"]["attention_count"] == 1


async def test_producer_can_read_channel_recommendations(monkeypatch):
    def fake_recommend_channels(**kwargs):
        assert kwargs == {
            "event_type": "OPPORTUNITY_PUBLISHED",
            "audience": "DISTRIBUTOR",
            "target_channels": ["WHATSAPP"],
        }
        return {
            "status": "READY",
            "top_channel": {"channel_code": "WHATSAPP"},
            "items": [],
        }

    monkeypatch.setattr(producer_supply, "recommend_channels", fake_recommend_channels)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/INSURECO/supply/channel-recommendations?event_type=OPPORTUNITY_PUBLISHED&audience=DISTRIBUTOR&target_channels=WHATSAPP",
            headers=PRODUCER_HEADERS,
        )

    assert response.status_code == 200
    assert (
        response.json()["recommendations"]["top_channel"]["channel_code"] == "WHATSAPP"
    )


async def test_producer_can_read_channel_readiness(monkeypatch):
    def fake_get_channel_readiness():
        return {
            "status": "ATTENTION",
            "summary": {"ready_count": 1, "count": 3},
            "items": [],
        }

    monkeypatch.setattr(
        producer_supply, "get_channel_readiness", fake_get_channel_readiness
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/INSURECO/supply/channel-readiness",
            headers=PRODUCER_HEADERS,
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == "Producer - Supply"
    assert payload["tenant_code"] == "FNB"
    assert payload["producer_code"] == "INSURECO"
    assert payload["readiness"]["summary"]["ready_count"] == 1


async def test_create_producer_supply_launch_creates_campaign_and_opportunity(
    monkeypatch,
):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())
    campaign_calls = {}
    opportunity_calls = {}

    async def fake_create_campaign(**kwargs):
        campaign_calls.update(kwargs)
        return {"ok": True, "campaign_code": "SWITCH_SALARY", "mode": "MIGRATED"}, 201

    async def fake_create_opportunity(**kwargs):
        opportunity_calls.update(kwargs)
        return opportunity_payload(opportunity_id)

    monkeypatch.setattr(producer_supply, "create_campaign", fake_create_campaign)
    monkeypatch.setattr(producer_supply, "create_opportunity", fake_create_opportunity)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.post(
            "/v1/tenants/FNB/producers/BOXER/supply/launches",
            json={
                "campaign_name": "Switch your salary",
                "campaign_code": "SWITCH_SALARY",
                "segment": "BANKING",
                "opportunity_title": "Switch your salary",
                "description": "Acquire salary switchers",
                "product_code": "TRANSACTIONAL_ACCOUNT",
                "product_name": "Transactional account",
                "target_segments": ["BANKING"],
                "target_regions": ["ZA"],
                "target_channels": ["WHATSAPP"],
                "distributor_types": ["BROKER"],
                "estimated_reward_amount": "100.00",
                "estimated_commission_amount": "25.00",
                "total_budget": "10000.00",
                "max_allocations": 100,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["mode"] == "draft"
    assert body["producer_code"] == "BOXER"
    assert body["campaign"]["campaign_code"] == "SWITCH_SALARY"
    assert body["opportunity"]["opportunity_id"] == opportunity_id
    assert campaign_calls["tenant_code"] == "FNB"
    assert campaign_calls["campaign_code"] == "SWITCH_SALARY"
    assert campaign_calls["attributes"]["source"] == "producer_supply_api"
    assert opportunity_calls["sponsor_code"] == "BOXER"
    assert opportunity_calls["campaign_code"] == "SWITCH_SALARY"
    assert opportunity_calls["opportunity_code"] == "SWITCH_SALARY-OPP"


async def test_create_producer_supply_launch_can_publish(monkeypatch):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())
    publish_calls = {}

    async def fake_create_campaign(**kwargs):
        return {"ok": True, "campaign_code": "PUBLISHED_SUPPLY"}, 201

    async def fake_create_opportunity(**kwargs):
        return opportunity_payload(opportunity_id)

    async def fake_publish_opportunity(**kwargs):
        publish_calls.update(kwargs)
        return opportunity_payload(opportunity_id, status="PUBLISHED")

    monkeypatch.setattr(producer_supply, "create_campaign", fake_create_campaign)
    monkeypatch.setattr(producer_supply, "create_opportunity", fake_create_opportunity)
    monkeypatch.setattr(
        producer_supply, "publish_opportunity", fake_publish_opportunity
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.post(
            "/v1/tenants/FNB/producers/BOXER/supply/launches",
            json={
                "campaign_name": "Published supply",
                "segment": "BANKING",
                "opportunity_title": "Published supply",
                "publish_now": True,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["mode"] == "published"
    assert body["opportunity"]["opportunity_status"] == "PUBLISHED"
    assert publish_calls == {"opportunity_id": opportunity_id}


async def test_create_producer_supply_launch_blocks_wrong_tenant_key(monkeypatch):
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"x-api-key": "test-pnp-key"},
    ) as client:
        response = await client.post(
            "/v1/tenants/FNB/producers/BOXER/supply/launches",
            json={
                "campaign_name": "Wrong tenant",
                "segment": "BANKING",
                "opportunity_title": "Wrong tenant",
            },
        )

    assert response.status_code == 403


async def test_list_producer_supply_opportunities_scopes_to_producer(monkeypatch):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_list_opportunities(**kwargs):
        calls.update(kwargs)
        return [opportunity_payload(opportunity_id, status="PUBLISHED")]

    monkeypatch.setattr(producer_supply, "list_opportunities", fake_list_opportunities)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/BOXER/supply/opportunities",
            params={"opportunity_status": "published", "limit": 10},
        )

    assert response.status_code == 200
    assert response.json()[0]["opportunity_id"] == opportunity_id
    assert calls["tenant_code"] == "FNB"
    assert calls["sponsor_code"] == "BOXER"
    assert calls["opportunity_status"] == "PUBLISHED"
    assert calls["limit"] == 10


async def test_get_producer_supply_performance_overview_scopes_to_producer(monkeypatch):
    from apps.api.routers import producer_supply

    calls = {}

    async def fake_get_marketplace_overview(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "sponsor_code": "BOXER",
            "campaign_code": None,
            "distributors": {"total_count": 10, "active_count": 8},
            "opportunities": {"total_count": 4, "published_count": 3},
            "routes": {
                "total_count": 20,
                "accepted_count": 5,
                "acceptance_rate": Decimal("0.2500"),
            },
            "commissions": {
                "event_count": 3,
                "total_commission_amount": Decimal("150.00"),
            },
            "wallets": {"wallet_count": 2, "current_balance": Decimal("100.00")},
            "governance": {"open_dispute_count": 1},
        }

    monkeypatch.setattr(
        producer_supply, "get_marketplace_overview", fake_get_marketplace_overview
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/BOXER/supply/performance/overview",
        )

    assert response.status_code == 200
    body = response.json()
    assert body["sponsor_code"] == "BOXER"
    assert body["routes"]["acceptance_rate"] == "0.2500"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": None,
    }


async def test_list_producer_supply_opportunity_performance_scopes_to_producer(
    monkeypatch,
):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_list_opportunity_performance(**kwargs):
        calls.update(kwargs)
        return [
            {
                "opportunity_id": opportunity_id,
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "campaign_code": "SWITCH_SALARY",
                "opportunity_code": "SWITCH_SALARY-OPP",
                "title": "Switch your salary",
                "opportunity_status": "PUBLISHED",
                "total_budget": Decimal("10000.00"),
                "remaining_budget": Decimal("9000.00"),
                "routed_count": 10,
                "accepted_count": 4,
                "declined_count": 2,
                "average_route_score": Decimal("87.50"),
                "conversion_count": 3,
                "completed_conversion_count": 1,
                "conversion_completion_rate": Decimal("0.3333"),
                "dispute_count": 0,
            }
        ]

    monkeypatch.setattr(
        producer_supply,
        "list_opportunity_performance",
        fake_list_opportunity_performance,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/BOXER/supply/performance/opportunities",
            params={"opportunity_status": "published", "limit": 10},
        )

    assert response.status_code == 200
    assert response.json()[0]["accepted_count"] == 4
    assert response.json()[0]["conversion_count"] == 3
    assert response.json()[0]["completed_conversion_count"] == 1
    assert response.json()[0]["conversion_completion_rate"] == "0.3333"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": None,
        "opportunity_status": "PUBLISHED",
        "limit": 10,
    }


async def test_list_producer_supply_conversions_scopes_to_producer(monkeypatch):
    from apps.api.routers import producer_supply

    referral_track_id = str(uuid4())
    opportunity_id = str(uuid4())
    route_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_list_producer_conversion_journeys(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "producer_code": "BOXER",
            "campaign_code": "SWITCH_SALARY",
            "opportunity_id": opportunity_id,
            "count": 1,
            "completed_count": 0,
            "completion_rate": Decimal("0.0000"),
            "items": [
                producer_conversion_payload(
                    referral_track_id=referral_track_id,
                    opportunity_id=opportunity_id,
                    route_id=route_id,
                    distributor_id=distributor_id,
                )
            ],
        }

    monkeypatch.setattr(
        producer_supply,
        "list_producer_conversion_journeys",
        fake_list_producer_conversion_journeys,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/BOXER/supply/conversions",
            params={
                "campaign_code": "switch_salary",
                "opportunity_id": opportunity_id,
                "limit": 10,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["completion_rate"] == "0.0000"
    assert body["items"][0]["referral_track_id"] == referral_track_id
    assert body["items"][0]["distributor_code"] == "DIST001"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "SWITCH_SALARY",
        "opportunity_id": opportunity_id,
        "limit": 10,
    }


async def test_update_producer_supply_opportunity_edits_draft(monkeypatch):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())
    update_calls = {}

    async def fake_get_opportunity(**kwargs):
        return opportunity_payload(opportunity_id, status="DRAFT")

    async def fake_update_opportunity(**kwargs):
        update_calls.update(kwargs)
        payload = opportunity_payload(opportunity_id, status="DRAFT")
        payload["title"] = kwargs["title"]
        return payload

    monkeypatch.setattr(producer_supply, "get_opportunity", fake_get_opportunity)
    monkeypatch.setattr(producer_supply, "update_opportunity", fake_update_opportunity)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.patch(
            f"/v1/tenants/FNB/producers/BOXER/supply/opportunities/{opportunity_id}",
            json={"title": "Updated supply", "total_budget": "15000.00"},
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated supply"
    assert update_calls["opportunity_id"] == opportunity_id
    assert update_calls["title"] == "Updated supply"
    assert str(update_calls["total_budget"]) == "15000.00"


async def test_update_producer_supply_opportunity_blocks_non_draft(monkeypatch):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())

    async def fake_get_opportunity(**kwargs):
        return opportunity_payload(opportunity_id, status="PUBLISHED")

    monkeypatch.setattr(producer_supply, "get_opportunity", fake_get_opportunity)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.patch(
            f"/v1/tenants/FNB/producers/BOXER/supply/opportunities/{opportunity_id}",
            json={"title": "Should not update"},
        )

    assert response.status_code == 409
    assert "Cannot edit" in response.json()["detail"]


async def test_producer_supply_opportunity_publish_close_reopen(monkeypatch):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())
    states = iter(["DRAFT", "PUBLISHED", "CLOSED"])
    action_calls = []

    async def fake_get_opportunity(**kwargs):
        return opportunity_payload(opportunity_id, status=next(states))

    async def fake_publish_opportunity(**kwargs):
        action_calls.append(("publish", kwargs))
        return opportunity_payload(opportunity_id, status="PUBLISHED")

    async def fake_close_opportunity(**kwargs):
        action_calls.append(("close", kwargs))
        return opportunity_payload(opportunity_id, status="CLOSED")

    async def fake_reopen_opportunity(**kwargs):
        action_calls.append(("reopen", kwargs))
        return opportunity_payload(opportunity_id, status="PUBLISHED")

    monkeypatch.setattr(producer_supply, "get_opportunity", fake_get_opportunity)
    monkeypatch.setattr(
        producer_supply, "publish_opportunity", fake_publish_opportunity
    )
    monkeypatch.setattr(producer_supply, "close_opportunity", fake_close_opportunity)
    monkeypatch.setattr(producer_supply, "reopen_opportunity", fake_reopen_opportunity)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        publish_response = await client.post(
            f"/v1/tenants/FNB/producers/BOXER/supply/opportunities/{opportunity_id}/publish"
        )
        close_response = await client.post(
            f"/v1/tenants/FNB/producers/BOXER/supply/opportunities/{opportunity_id}/close"
        )
        reopen_response = await client.post(
            f"/v1/tenants/FNB/producers/BOXER/supply/opportunities/{opportunity_id}/reopen"
        )

    assert publish_response.status_code == 200
    assert close_response.status_code == 200
    assert reopen_response.status_code == 200
    assert publish_response.json()["opportunity_status"] == "PUBLISHED"
    assert close_response.json()["opportunity_status"] == "CLOSED"
    assert reopen_response.json()["opportunity_status"] == "PUBLISHED"
    assert action_calls == [
        ("publish", {"opportunity_id": opportunity_id}),
        ("close", {"opportunity_id": opportunity_id}),
        ("reopen", {"opportunity_id": opportunity_id}),
    ]


async def test_producer_supply_opportunity_blocks_other_producer(monkeypatch):
    from apps.api.routers import producer_supply

    opportunity_id = str(uuid4())

    async def fake_get_opportunity(**kwargs):
        payload = opportunity_payload(opportunity_id, status="DRAFT")
        payload["sponsor_code"] = "OTHER"
        return payload

    monkeypatch.setattr(producer_supply, "get_opportunity", fake_get_opportunity)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/tenants/FNB/producers/BOXER/supply/opportunities/{opportunity_id}"
        )

    assert response.status_code == 404


async def test_producer_supply_insurance_proof_is_scoped_to_producer(monkeypatch):
    from apps.api.routers import producer_supply

    async def fake_get_producer_insurance_journey_proof(**kwargs):
        return {
            "scope": "producer",
            "surface": "Producer - Supply",
            "tenant_code": kwargs["tenant_code"],
            "sponsor_code": kwargs["producer_code"],
            "status": "READY",
            "invoiced_amount": "250.00",
            "steps": [{"surface": "Producer - Supply", "status": "READY"}],
        }

    monkeypatch.setattr(
        producer_supply,
        "get_producer_insurance_journey_proof",
        fake_get_producer_insurance_journey_proof,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/INSURECO/supply/proof/insurance"
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope"] == "producer"
    assert payload["surface"] == "Producer - Supply"
    assert payload["tenant_code"] == "FNB"
    assert payload["sponsor_code"] == "INSURECO"
    assert payload["steps"][0]["surface"] == "Producer - Supply"


async def test_producer_supply_insurance_proof_rejects_other_producer_key(monkeypatch):
    from apps.api.routers import producer_supply

    async def fake_get_producer_insurance_journey_proof(**kwargs):
        return {"status": "READY"}

    monkeypatch.setattr(
        producer_supply,
        "get_producer_insurance_journey_proof",
        fake_get_producer_insurance_journey_proof,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PRODUCER_HEADERS
    ) as client:
        response = await client.get(
            "/v1/tenants/FNB/producers/OTHER/supply/proof/insurance"
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "API key is not authorised for this producer"
