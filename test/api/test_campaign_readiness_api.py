from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import admin_campaign_readiness

pytestmark = pytest.mark.asyncio

DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}
PLATFORM_ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def _readiness(
    *,
    readiness: str = "READY",
    blockers: list[dict] | None = None,
    warnings: list[dict] | None = None,
) -> dict:
    return {
        "readiness": readiness,
        "can_proceed": readiness != "NOT_READY",
        "operation": "CONTROL_PLANE_VIEW",
        "tenant_code": "FNB",
        "campaign_code": "CAMP001",
        "opportunity_id": None,
        "blockers": blockers or [],
        "warnings": warnings or [],
        "unknowns": [],
        "evidence": {
            "campaign": {
                "source": "marketing_campaigns",
                "campaign_status": "ACTIVE",
            }
        },
        "evaluated_at": "2026-06-25T00:00:00+00:00",
    }


async def test_distribution_admin_can_fetch_campaign_readiness(monkeypatch):
    calls = []

    async def fake_get_campaign_readiness(**kwargs):
        calls.append(kwargs)
        return _readiness()

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={"tenant_code": "fnb"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["readiness"]["readiness"] == "READY"
    assert body["guardrail"].startswith("Read-only admin campaign readiness")
    assert calls == [
        {
            "tenant_code": "FNB",
            "campaign_code": "CAMP001",
            "operation": "CONTROL_PLANE_VIEW",
            "opportunity_id": None,
            "include_evidence": True,
        }
    ]


async def test_platform_admin_can_fetch_campaign_readiness(monkeypatch):
    async def fake_get_campaign_readiness(**kwargs):
        return _readiness()

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PLATFORM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200


async def test_campaign_readiness_forwards_operation_scope(monkeypatch):
    calls = []

    async def fake_get_campaign_readiness(**kwargs):
        calls.append(kwargs)
        return _readiness(readiness="UNKNOWN")

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={
                "tenant_code": "FNB",
                "operation": "PUBLISH_OPPORTUNITY",
                "opportunity_id": "OPP-1",
                "include_evidence": "false",
            },
        )

    assert response.status_code == 200
    assert calls == [
        {
            "tenant_code": "FNB",
            "campaign_code": "CAMP001",
            "operation": "PUBLISH_OPPORTUNITY",
            "opportunity_id": "OPP-1",
            "include_evidence": False,
        }
    ]


async def test_campaign_readiness_returns_401_without_credentials(monkeypatch):
    async def fake_get_campaign_readiness(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 401


async def test_campaign_readiness_rejects_adjacent_admin_role(monkeypatch):
    async def fake_get_campaign_readiness(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"x-api-key": "test-finance-admin-key"},
    ) as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 403


async def test_campaign_readiness_returns_400_for_invalid_operation(monkeypatch):
    async def fake_get_campaign_readiness(**kwargs):
        raise ValueError("Unsupported campaign readiness operation: DO_SOMETHING")

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={"tenant_code": "FNB", "operation": "DO_SOMETHING"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported campaign readiness operation: DO_SOMETHING",
    }


@pytest.mark.parametrize("code", ["CAMPAIGN_NOT_FOUND", "TENANT_MISMATCH"])
async def test_campaign_readiness_returns_404_for_inaccessible_campaign(
    monkeypatch, code
):
    async def fake_get_campaign_readiness(**kwargs):
        return _readiness(
            readiness="NOT_READY",
            blockers=[
                {
                    "code": code,
                    "severity": "BLOCKER",
                    "message": "Not accessible.",
                }
            ],
        )

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "code": "campaign_readiness_not_found",
        "message": "Campaign readiness was not found for the requested tenant.",
    }


async def test_campaign_readiness_preserves_non_ready_response(monkeypatch):
    async def fake_get_campaign_readiness(**kwargs):
        return _readiness(
            readiness="NOT_READY",
            blockers=[
                {
                    "code": "CAMPAIGN_INACTIVE",
                    "severity": "BLOCKER",
                    "message": "Campaign is inactive.",
                }
            ],
        )

    monkeypatch.setattr(
        admin_campaign_readiness,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/campaigns/CAMP001/readiness",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200
    assert response.json()["readiness"]["blockers"][0]["code"] == "CAMPAIGN_INACTIVE"
