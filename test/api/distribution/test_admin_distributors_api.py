from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from apps.api.main import app


ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


pytestmark = pytest.mark.asyncio


async def test_create_distributor(monkeypatch):
    from apps.api.routers.distribution import admin_distributors

    distributor_id = str(uuid4())
    calls = {}

    async def fake_create_distributor(**kwargs):
        calls.update(kwargs)
        return {
            "distributor_id": distributor_id,
            "tenant_code": kwargs["tenant_code"],
            "distributor_code": kwargs["distributor_code"],
            "distributor_name": kwargs["distributor_name"],
            "distributor_type": kwargs["distributor_type"],
            "status": "ONBOARDING",
            "segments": kwargs["segments"],
            "regions": kwargs["regions"],
        }

    monkeypatch.setattr(
        admin_distributors,
        "create_distributor",
        fake_create_distributor,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/distributors",
            json={
                "tenant_code": "FNB",
                "distributor_code": "CALL_CENTRE_001",
                "distributor_name": "Cape Town Sales Desk",
                "distributor_type": "CALL_CENTRE",
                "contact_email": "sales@example.com",
                "contact_phone": "+27110000000",
                "channels": ["PHONE", "WHATSAPP"],
                "segments": ["MASS_MARKET"],
                "regions": ["ZA-WC"],
                "capabilities": {"languages": ["en", "zu"]},
                "eligibility": {"kyb_status": "PENDING"},
                "operating_limits": {"daily_leads": 250},
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["distributor"]["distributor_id"] == distributor_id
    assert body["distributor"]["status"] == "ONBOARDING"
    assert calls == {
        "tenant_code": "FNB",
        "distributor_code": "CALL_CENTRE_001",
        "distributor_name": "Cape Town Sales Desk",
        "distributor_type": "CALL_CENTRE",
        "contact_email": "sales@example.com",
        "contact_phone": "+27110000000",
        "channels": ["PHONE", "WHATSAPP"],
        "segments": ["MASS_MARKET"],
        "regions": ["ZA-WC"],
        "capabilities": {"languages": ["en", "zu"]},
        "eligibility": {"kyb_status": "PENDING"},
        "operating_limits": {"daily_leads": 250},
        "metadata": {"source": "test"},
    }


async def test_list_distributors(monkeypatch):
    from apps.api.routers.distribution import admin_distributors

    distributor_id = str(uuid4())
    calls = {}

    async def fake_list_distributors(**kwargs):
        calls.update(kwargs)
        return [
            {
                "distributor_id": distributor_id,
                "tenant_code": "FNB",
                "distributor_code": "AGENCY_001",
                "status": "ACTIVE",
            }
        ]

    monkeypatch.setattr(
        admin_distributors,
        "list_distributors",
        fake_list_distributors,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            "/admin/distribution/distributors",
            params={
                "tenant_code": "FNB",
                "status": "ACTIVE",
                "distributor_type": "AGENCY",
                "segment": "AFFLUENT",
                "region": "ZA-GP",
                "limit": 25,
            },
        )

    assert response.status_code == 200
    body = response.json()

    assert body["tenant_code"] == "FNB"
    assert body["count"] == 1
    assert body["items"][0]["distributor_id"] == distributor_id
    assert calls == {
        "tenant_code": "FNB",
        "status": "ACTIVE",
        "distributor_type": "AGENCY",
        "segment": "AFFLUENT",
        "region": "ZA-GP",
        "limit": 25,
    }


async def test_get_distributor(monkeypatch):
    from apps.api.routers.distribution import admin_distributors

    distributor_id = str(uuid4())

    async def fake_get_distributor(**kwargs):
        return {
            "distributor_id": kwargs["distributor_id"],
            "distributor_code": "FIELD_001",
            "status": "ACTIVE",
        }

    monkeypatch.setattr(
        admin_distributors,
        "get_distributor",
        fake_get_distributor,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/distribution/distributors/{distributor_id}",
        )

    assert response.status_code == 200
    assert response.json()["distributor"] == {
        "distributor_id": distributor_id,
        "distributor_code": "FIELD_001",
        "status": "ACTIVE",
    }


async def test_update_distributor_profile(monkeypatch):
    from apps.api.routers.distribution import admin_distributors

    distributor_id = str(uuid4())
    calls = {}

    async def fake_update_distributor_profile(**kwargs):
        calls.update(kwargs)
        return {
            "distributor_id": kwargs["distributor_id"],
            "distributor_name": kwargs["distributor_name"],
            "segments": kwargs["segments"],
            "operating_limits": kwargs["operating_limits"],
        }

    monkeypatch.setattr(
        admin_distributors,
        "update_distributor_profile",
        fake_update_distributor_profile,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.patch(
            f"/admin/distribution/distributors/{distributor_id}/profile",
            json={
                "distributor_name": "Updated Distributor",
                "segments": ["SME"],
                "operating_limits": {"daily_leads": 100},
            },
        )

    assert response.status_code == 200
    assert response.json()["distributor"]["distributor_name"] == "Updated Distributor"
    assert calls == {
        "distributor_id": distributor_id,
        "distributor_name": "Updated Distributor",
        "contact_email": None,
        "contact_phone": None,
        "channels": None,
        "segments": ["SME"],
        "regions": None,
        "capabilities": None,
        "eligibility": None,
        "operating_limits": {"daily_leads": 100},
        "metadata": None,
    }


@pytest.mark.parametrize(
    ("endpoint", "expected_status"),
    [
        ("activate", "ACTIVE"),
        ("suspend", "SUSPENDED"),
        ("terminate", "TERMINATED"),
    ],
)
async def test_distributor_status_changes(monkeypatch, endpoint, expected_status):
    from apps.api.routers.distribution import admin_distributors

    distributor_id = str(uuid4())

    async def fake_status_change(**kwargs):
        return {
            "distributor_id": kwargs["distributor_id"],
            "status": expected_status,
        }

    monkeypatch.setattr(
        admin_distributors,
        f"{endpoint}_distributor",
        fake_status_change,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            f"/admin/distribution/distributors/{distributor_id}/{endpoint}",
        )

    assert response.status_code == 200
    assert response.json()["distributor"] == {
        "distributor_id": distributor_id,
        "status": expected_status,
    }


async def test_duplicate_distributor_returns_409(monkeypatch):
    from apps.api.routers.distribution import admin_distributors

    async def fake_create_distributor(**kwargs):
        raise admin_distributors.DistributorDuplicate(
            "Distributor already exists for tenant"
        )

    monkeypatch.setattr(
        admin_distributors,
        "create_distributor",
        fake_create_distributor,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.post(
            "/admin/distribution/distributors",
            json={
                "tenant_code": "FNB",
                "distributor_code": "DUPLICATE",
                "distributor_name": "Duplicate",
                "distributor_type": "AGENCY",
            },
        )

    assert response.status_code == 409
    assert response.json() == {"detail": "Distributor already exists for tenant"}


async def test_missing_distributor_returns_404(monkeypatch):
    from apps.api.routers.distribution import admin_distributors

    async def fake_get_distributor(**kwargs):
        raise admin_distributors.DistributorNotFound("Distributor not found")

    monkeypatch.setattr(
        admin_distributors,
        "get_distributor",
        fake_get_distributor,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=ADMIN_HEADERS) as client:
        response = await client.get(
            f"/admin/distribution/distributors/{uuid4()}",
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Distributor not found"}
