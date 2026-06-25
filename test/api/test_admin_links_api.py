from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import admin_links

pytestmark = pytest.mark.asyncio

DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}
PLATFORM_ADMIN_HEADERS = {"x-api-key": "test-admin-key"}


def _link_code(*, status: str = "ISSUED") -> dict:
    return {
        "link_code_id": "referrer_codes:code-1",
        "source_type": "REFERRAL_CODE",
        "source": "referrer_codes",
        "tenant_code": "FNB",
        "status": status,
        "code": "REF123",
        "campaign": {"campaign_code": None, "campaign_track_id": None},
        "participant": {
            "participant_type": "REFERRER",
            "participant_ref": "SafeHandle",
            "source": "referrer_codes",
        },
        "attribution": {
            "referral_track_id": None,
            "route_id": None,
            "opportunity_id": None,
        },
        "metadata": {},
        "evidence": {
            "referral_code": "REF123",
            "referrer_ucn": "[REDACTED]",
            "referrer_ucn_hash": "[REDACTED]",
        },
        "missing_evidence": [],
        "source_warnings": [],
        "redactions": ["referrer_ucn", "referrer_ucn_hash"],
        "created_at": "2026-06-25T00:00:00+00:00",
        "updated_at": "2026-06-25T00:00:00+00:00",
        "inspected_at": "2026-06-25T00:00:00+00:00",
    }


async def test_distribution_admin_can_inspect_link_code(monkeypatch):
    calls = []

    async def fake_inspect_link_code(**kwargs):
        calls.append(kwargs)
        return _link_code()

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "fnb",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["link_code"]["status"] == "ISSUED"
    assert body["link_code"]["evidence"]["referrer_ucn"] == "[REDACTED]"
    assert body["guardrail"].startswith("Read-only admin link/code inspection")
    assert calls == [
        {
            "tenant_code": "FNB",
            "source_type": "REFERRAL_CODE",
            "link_code_id": None,
            "code_or_ref": "REF123",
            "include_evidence": True,
        }
    ]


async def test_platform_admin_can_inspect_link_code(monkeypatch):
    async def fake_inspect_link_code(**kwargs):
        return _link_code()

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(
        app=app, base_url="http://test", headers=PLATFORM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "CAMPAIGN_CODE",
                "code_or_ref": "CAMP001",
            },
        )

    assert response.status_code == 200


async def test_link_code_inspect_forwards_link_id_and_evidence_flag(monkeypatch):
    calls = []

    async def fake_inspect_link_code(**kwargs):
        calls.append(kwargs)
        result = _link_code(status="ACTIVE")
        result["evidence"] = None
        return result

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "ROUTE_REFERRAL_LINK",
                "link_code_id": "route-1:referral-1",
                "include_evidence": "false",
            },
        )

    assert response.status_code == 200
    assert response.json()["link_code"]["evidence"] is None
    assert calls == [
        {
            "tenant_code": "FNB",
            "source_type": "ROUTE_REFERRAL_LINK",
            "link_code_id": "route-1:referral-1",
            "code_or_ref": None,
            "include_evidence": False,
        }
    ]


async def test_link_code_inspect_returns_401_without_credentials(monkeypatch):
    async def fake_inspect_link_code(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 401


async def test_link_code_inspect_rejects_adjacent_admin_role(monkeypatch):
    async def fake_inspect_link_code(**kwargs):  # pragma: no cover
        raise AssertionError("service should not be called")

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"x-api-key": "test-finance-admin-key"},
    ) as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "error_message",
    [
        "Unsupported link/code source_type: BAD_SOURCE",
        "link_code_id or code_or_ref is required",
    ],
)
async def test_link_code_inspect_returns_safe_validation_error(
    monkeypatch, error_message
):
    async def fake_inspect_link_code(**kwargs):
        raise ValueError(error_message)

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "BAD_SOURCE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": error_message,
    }


async def test_link_code_inspect_preserves_missing_evidence_result(monkeypatch):
    async def fake_inspect_link_code(**kwargs):
        result = _link_code(status="INVALID")
        result["missing_evidence"] = [
            {
                "code": "SOURCE_NOT_FOUND",
                "severity": "BLOCKER",
                "source": "referrer_codes",
                "message": "Source evidence was not found for the requested tenant.",
            }
        ]
        return result

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "MISSING",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["link_code"]["status"] == "INVALID"
    assert body["link_code"]["missing_evidence"][0]["code"] == "SOURCE_NOT_FOUND"


async def test_link_code_inspect_preserves_unknown_source_warning(monkeypatch):
    async def fake_inspect_link_code(**kwargs):
        result = _link_code(status="UNKNOWN")
        result["source_warnings"] = [
            {
                "code": "SOURCE_UNAVAILABLE",
                "severity": "WARNING",
                "source": "referrer_codes",
                "message": "Source evidence could not be inspected safely.",
            }
        ]
        return result

    monkeypatch.setattr(admin_links, "inspect_link_code", fake_inspect_link_code)

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/links/inspect",
            params={
                "tenant_code": "FNB",
                "source_type": "REFERRAL_CODE",
                "code_or_ref": "REF123",
            },
        )

    assert response.status_code == 200
    assert response.json()["link_code"]["status"] == "UNKNOWN"
    assert response.json()["link_code"]["source_warnings"][0]["code"] == (
        "SOURCE_UNAVAILABLE"
    )
