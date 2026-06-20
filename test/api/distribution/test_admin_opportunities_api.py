from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


def opportunity_payload(opportunity_id: str, **overrides):
    payload = {
        "opportunity_id": opportunity_id,
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "campaign_code": "BOXER_ACQ",
        "funding_contract_id": None,
        "opportunity_code": "BOXER_HOME_LOANS",
        "title": "Boxer Home Loans",
        "description": "Funded acquisition opportunity",
        "product_code": "HOME_LOAN",
        "product_name": "Home Loan",
        "opportunity_status": "DRAFT",
        "target_segments": ["MASS_MARKET"],
        "target_regions": ["ZA-GP"],
        "target_channels": ["FIELD"],
        "distributor_types": ["AGENCY"],
        "commission_rule_id": None,
        "estimated_reward_amount": Decimal("100.00"),
        "estimated_commission_amount": Decimal("50.00"),
        "total_budget": Decimal("100000.00"),
        "remaining_budget": Decimal("100000.00"),
        "max_allocations": 1000,
        "remaining_allocations": 1000,
        "starts_at": "2026-06-12T10:00:00",
        "ends_at": "2026-12-31T23:59:59",
        "published_at": None,
        "closed_at": None,
        "metadata": {"source": "test"},
        "created_at": "2026-06-12T10:00:00",
        "updated_at": "2026-06-12T10:00:00",
    }
    payload.update(overrides)
    return payload


async def test_create_opportunity(monkeypatch):
    from apps.api.routers.distribution import admin_opportunities

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_create_opportunity(**kwargs):
        calls.update(kwargs)
        return opportunity_payload(opportunity_id)

    monkeypatch.setattr(
        admin_opportunities,
        "create_opportunity",
        fake_create_opportunity,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/opportunities",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "opportunity_code": "BOXER_HOME_LOANS",
                "title": "Boxer Home Loans",
                "description": "Funded acquisition opportunity",
                "campaign_code": "BOXER_ACQ",
                "product_code": "HOME_LOAN",
                "product_name": "Home Loan",
                "target_segments": ["MASS_MARKET"],
                "target_regions": ["ZA-GP"],
                "target_channels": ["FIELD"],
                "distributor_types": ["AGENCY"],
                "estimated_reward_amount": "100.00",
                "estimated_commission_amount": "50.00",
                "total_budget": "100000.00",
                "max_allocations": 1000,
                "starts_at": "2026-06-12T10:00:00",
                "ends_at": "2026-12-31T23:59:59",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["opportunity_id"] == opportunity_id
    assert body["opportunity_status"] == "DRAFT"
    assert calls == {
        "tenant_code": "FNB",
        "sponsor_code": "BOXER",
        "opportunity_code": "BOXER_HOME_LOANS",
        "title": "Boxer Home Loans",
        "description": "Funded acquisition opportunity",
        "campaign_code": "BOXER_ACQ",
        "funding_contract_id": None,
        "product_code": "HOME_LOAN",
        "product_name": "Home Loan",
        "target_segments": ["MASS_MARKET"],
        "target_regions": ["ZA-GP"],
        "target_channels": ["FIELD"],
        "distributor_types": ["AGENCY"],
        "commission_rule_id": None,
        "estimated_reward_amount": Decimal("100.00"),
        "estimated_commission_amount": Decimal("50.00"),
        "total_budget": Decimal("100000.00"),
        "max_allocations": 1000,
        "starts_at": datetime(2026, 6, 12, 10, 0, 0),
        "ends_at": datetime(2026, 12, 31, 23, 59, 59),
        "metadata": {"source": "test"},
    }


async def test_list_opportunities(monkeypatch):
    from apps.api.routers.distribution import admin_opportunities

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_list_opportunities(**kwargs):
        calls.update(kwargs)
        return [opportunity_payload(opportunity_id, opportunity_status="PUBLISHED")]

    monkeypatch.setattr(
        admin_opportunities,
        "list_opportunities",
        fake_list_opportunities,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/opportunities",
            params={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "campaign_code": "BOXER_ACQ",
                "opportunity_status": "PUBLISHED",
                "segment": "MASS_MARKET",
                "region": "ZA-GP",
                "channel": "FIELD",
                "distributor_type": "AGENCY",
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
        "segment": "MASS_MARKET",
        "region": "ZA-GP",
        "channel": "FIELD",
        "distributor_type": "AGENCY",
        "limit": 25,
    }


async def test_get_opportunity(monkeypatch):
    from apps.api.routers.distribution import admin_opportunities

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_get_opportunity(**kwargs):
        calls.update(kwargs)
        return opportunity_payload(opportunity_id)

    monkeypatch.setattr(
        admin_opportunities,
        "get_opportunity",
        fake_get_opportunity,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/distribution/opportunities/{opportunity_id}")

    assert response.status_code == 200
    assert response.json()["opportunity_id"] == opportunity_id
    assert calls == {"opportunity_id": opportunity_id}


async def test_update_opportunity(monkeypatch):
    from apps.api.routers.distribution import admin_opportunities

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_update_opportunity(**kwargs):
        calls.update(kwargs)
        return opportunity_payload(
            opportunity_id,
            title="Updated opportunity",
            target_regions=["ZA-WC"],
        )

    monkeypatch.setattr(
        admin_opportunities,
        "update_opportunity",
        fake_update_opportunity,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.patch(
            f"/admin/distribution/opportunities/{opportunity_id}",
            json={
                "title": "Updated opportunity",
                "target_regions": ["ZA-WC"],
                "total_budget": "120000.00",
                "metadata": {"source": "update"},
            },
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated opportunity"
    assert calls == {
        "opportunity_id": opportunity_id,
        "title": "Updated opportunity",
        "description": None,
        "product_code": None,
        "product_name": None,
        "target_segments": None,
        "target_regions": ["ZA-WC"],
        "target_channels": None,
        "distributor_types": None,
        "commission_rule_id": None,
        "estimated_reward_amount": None,
        "estimated_commission_amount": None,
        "total_budget": Decimal("120000.00"),
        "max_allocations": None,
        "starts_at": None,
        "ends_at": None,
        "metadata": {"source": "update"},
    }


@pytest.mark.parametrize(
    ("path", "service_name", "status_value"),
    [
        ("publish", "publish_opportunity", "PUBLISHED"),
        ("close", "close_opportunity", "CLOSED"),
        ("reopen", "reopen_opportunity", "PUBLISHED"),
    ],
)
async def test_opportunity_status_transitions(
    monkeypatch,
    path,
    service_name,
    status_value,
):
    from apps.api.routers.distribution import admin_opportunities

    opportunity_id = str(uuid4())
    calls = {}

    async def fake_transition(**kwargs):
        calls.update(kwargs)
        return opportunity_payload(opportunity_id, opportunity_status=status_value)

    monkeypatch.setattr(admin_opportunities, service_name, fake_transition)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/opportunities/{opportunity_id}/{path}"
        )

    assert response.status_code == 200
    assert response.json()["opportunity_status"] == status_value
    assert calls == {"opportunity_id": opportunity_id}


async def test_duplicate_opportunity_returns_409(monkeypatch):
    from apps.api.routers.distribution import admin_opportunities

    async def fake_create_opportunity(**kwargs):
        raise admin_opportunities.OpportunityDuplicate(
            "Opportunity already exists for tenant"
        )

    monkeypatch.setattr(
        admin_opportunities,
        "create_opportunity",
        fake_create_opportunity,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/opportunities",
            json={
                "tenant_code": "FNB",
                "sponsor_code": "BOXER",
                "opportunity_code": "BOXER_HOME_LOANS",
                "title": "Boxer Home Loans",
            },
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "Opportunity already exists for tenant"}


async def test_missing_opportunity_returns_404(monkeypatch):
    from apps.api.routers.distribution import admin_opportunities

    async def fake_get_opportunity(**kwargs):
        raise admin_opportunities.OpportunityNotFound("Opportunity not found")

    monkeypatch.setattr(
        admin_opportunities,
        "get_opportunity",
        fake_get_opportunity,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(f"/admin/distribution/opportunities/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Opportunity not found"}
