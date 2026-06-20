from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


def route_payload(route_id: str, opportunity_id: str, distributor_id: str, **overrides):
    payload = {
        "route_id": route_id,
        "tenant_code": "FNB",
        "opportunity_id": opportunity_id,
        "distributor_id": distributor_id,
        "route_status": "ROUTED",
        "route_score": Decimal("100.00"),
        "route_reasons": [
            "distributor_type: matched AGENCY",
            "segment: matched MASS_MARKET",
            "region: matched ZA-GP",
            "channel: matched FIELD",
        ],
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


def match_payload(opportunity_id: str, distributor_id: str, **overrides):
    payload = {
        "opportunity_id": opportunity_id,
        "distributor_id": distributor_id,
        "distributor_code": "AGENCY_001",
        "distributor_name": "Agency One",
        "distributor_type": "AGENCY",
        "route_score": Decimal("100.00"),
        "route_reasons": [
            "distributor_type: matched AGENCY",
            "segment: matched MASS_MARKET",
            "region: matched ZA-GP",
            "channel: matched FIELD",
        ],
    }
    payload.update(overrides)
    return payload


async def test_match_opportunity(monkeypatch):
    from apps.api.routers.distribution import admin_routing

    opportunity_id = str(uuid4())
    distributor_id = str(uuid4())
    calls = {}

    async def fake_match_distributors_for_opportunity(**kwargs):
        calls.update(kwargs)
        return {
            "opportunity_id": opportunity_id,
            "tenant_code": "FNB",
            "count": 1,
            "items": [match_payload(opportunity_id, distributor_id)],
        }

    monkeypatch.setattr(
        admin_routing,
        "match_distributors_for_opportunity",
        fake_match_distributors_for_opportunity,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/routing/opportunities/{opportunity_id}/matches",
            json={"minimum_score": "50", "limit": 10},
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["distributor_id"] == distributor_id
    assert calls == {
        "opportunity_id": opportunity_id,
        "minimum_score": Decimal("50"),
        "limit": 10,
    }


async def test_route_opportunity(monkeypatch):
    from apps.api.routers.distribution import admin_routing

    opportunity_id = str(uuid4())
    distributor_id = str(uuid4())
    route_id = str(uuid4())
    calls = {}

    async def fake_route_opportunity(**kwargs):
        calls.update(kwargs)
        return {
            "opportunity_id": opportunity_id,
            "tenant_code": "FNB",
            "count": 1,
            "items": [route_payload(route_id, opportunity_id, distributor_id)],
        }

    monkeypatch.setattr(admin_routing, "route_opportunity", fake_route_opportunity)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/routing/opportunities/{opportunity_id}/routes",
            json={
                "minimum_score": "75",
                "limit": 5,
                "expires_at": "2026-06-30T23:59:59",
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["items"][0]["route_id"] == route_id
    assert calls["opportunity_id"] == opportunity_id
    assert calls["minimum_score"] == Decimal("75")
    assert calls["limit"] == 5
    assert calls["expires_at"].isoformat() == "2026-06-30T23:59:59"
    assert calls["metadata"] == {"source": "test"}


async def test_list_offer_routes(monkeypatch):
    from apps.api.routers.distribution import admin_routing

    opportunity_id = str(uuid4())
    distributor_id = str(uuid4())
    route_id = str(uuid4())
    calls = {}

    async def fake_list_routes(**kwargs):
        calls.update(kwargs)
        return {
            "tenant_code": "FNB",
            "count": 1,
            "items": [route_payload(route_id, opportunity_id, distributor_id)],
        }

    monkeypatch.setattr(admin_routing, "list_routes", fake_list_routes)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/routing/routes",
            params={
                "tenant_code": "FNB",
                "opportunity_id": opportunity_id,
                "distributor_id": distributor_id,
                "route_status": "ROUTED",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["route_id"] == route_id
    assert calls == {
        "tenant_code": "FNB",
        "opportunity_id": opportunity_id,
        "distributor_id": distributor_id,
        "route_status": "ROUTED",
        "limit": 25,
    }


@pytest.mark.parametrize(
    ("endpoint", "service_name", "status_value"),
    [
        ("accept", "accept_route", "ACCEPTED"),
        ("decline", "decline_route", "DECLINED"),
    ],
)
async def test_route_status_changes(monkeypatch, endpoint, service_name, status_value):
    from apps.api.routers.distribution import admin_routing

    opportunity_id = str(uuid4())
    distributor_id = str(uuid4())
    route_id = str(uuid4())
    calls = {}

    async def fake_status_change(**kwargs):
        calls.update(kwargs)
        return route_payload(
            route_id,
            opportunity_id,
            distributor_id,
            route_status=status_value,
        )

    monkeypatch.setattr(admin_routing, service_name, fake_status_change)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/routing/routes/{route_id}/{endpoint}"
        )

    assert response.status_code == 200
    assert response.json()["route_status"] == status_value
    assert calls == {"route_id": route_id}


async def test_unpublished_opportunity_returns_409(monkeypatch):
    from apps.api.routers.distribution import admin_routing

    async def fake_match_distributors_for_opportunity(**kwargs):
        raise admin_routing.RoutingOpportunityNotRoutable(
            "Opportunity must be published before routing"
        )

    monkeypatch.setattr(
        admin_routing,
        "match_distributors_for_opportunity",
        fake_match_distributors_for_opportunity,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/routing/opportunities/{uuid4()}/matches",
            json={},
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "Opportunity must be published before routing"}


async def test_missing_route_returns_404(monkeypatch):
    from apps.api.routers.distribution import admin_routing

    async def fake_accept_route(**kwargs):
        raise admin_routing.RouteNotFound("Route not found")

    monkeypatch.setattr(admin_routing, "accept_route", fake_accept_route)

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/routing/routes/{uuid4()}/accept"
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Route not found"}
