from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import admin_outcomes
from services.outcome_trace_service import OutcomeTraceNotFound

pytestmark = pytest.mark.asyncio

TRACE_ID = "11111111-1111-4111-8111-111111111111"
SYSTEM_ADMIN_HEADERS = {"x-api-key": "test-system-admin-key"}


def _trace(*, completeness: str = "COMPLETE") -> dict:
    return {
        "trace_id": f"outcome:referral_track_id:{TRACE_ID}",
        "trace_type": "OUTCOME",
        "lookup": {"type": "REFERRAL_TRACK_ID", "value": TRACE_ID},
        "tenant_code": "FNB",
        "trace_completeness": completeness,
        "sections": {"outcome": {"referral_track_id": TRACE_ID}},
        "support_trace": {"audit_reference_count": 0},
        "missing_evidence": (
            []
            if completeness == "COMPLETE"
            else [
                {
                    "section": "reward",
                    "code": "NO_SOURCE_EVIDENCE",
                    "severity": "INFO",
                    "source": "rewards",
                    "message": "No reward evidence was found.",
                }
            ]
        ),
        "source_warnings": [],
        "redactions": [],
        "generated_at": "2026-06-22T00:00:00Z",
    }


async def test_system_admin_can_fetch_outcome_trace(monkeypatch):
    calls = []

    async def fake_get_outcome_trace(**kwargs):
        calls.append(kwargs)
        return _trace()

    monkeypatch.setattr(admin_outcomes, "get_outcome_trace", fake_get_outcome_trace)

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/trace",
            params={"tenant_code": "fnb"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["trace"]["trace_completeness"] == "COMPLETE"
    assert body["guardrail"].startswith("Read-only operator outcome trace")
    assert calls == [
        {
            "tenant_code": "FNB",
            "referral_track_id": TRACE_ID,
            "identity": {
                "authenticated": True,
                "role": "SYSTEM_ADMIN",
                "tenant_code": "INTERNAL",
                "tenant": "INTERNAL",
                "auth_source": "api_key",
            },
            "include_sections": None,
        }
    ]


@pytest.mark.parametrize(
    "headers",
    [
        {"x-api-key": "test-admin-key"},
        {"x-api-key": "test-finance-admin-key"},
        {"x-api-key": "test-distribution-admin-key"},
    ],
)
async def test_admin_outcome_trace_allows_operator_admin_roles(monkeypatch, headers):
    async def fake_get_outcome_trace(**kwargs):
        return _trace()

    monkeypatch.setattr(admin_outcomes, "get_outcome_trace", fake_get_outcome_trace)

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/trace",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200


async def test_admin_outcome_trace_returns_401_without_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/trace",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 401


async def test_admin_outcome_trace_rejects_non_operator_identity(monkeypatch):
    async def fake_get_outcome_trace(**kwargs):  # pragma: no cover - should not run
        raise AssertionError("service should not be called")

    monkeypatch.setattr(admin_outcomes, "get_outcome_trace", fake_get_outcome_trace)

    async with AsyncClient(
        app=app, base_url="http://test", headers={"x-api-key": "test-partner-key"}
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/trace",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_admin_outcome_trace_returns_404_for_missing_outcome(monkeypatch):
    async def fake_get_outcome_trace(**kwargs):
        raise OutcomeTraceNotFound("missing")

    monkeypatch.setattr(admin_outcomes, "get_outcome_trace", fake_get_outcome_trace)

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/trace",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "code": "outcome_not_found",
        "message": "Outcome trace was not found for the requested tenant.",
    }


async def test_admin_outcome_trace_returns_safe_validation_error(monkeypatch):
    async def fake_get_outcome_trace(**kwargs):
        raise ValueError("Unsupported outcome trace section: raw_payload")

    monkeypatch.setattr(admin_outcomes, "get_outcome_trace", fake_get_outcome_trace)

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/trace",
            params={"tenant_code": "FNB", "include_sections": ["raw_payload"]},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported outcome trace section: raw_payload",
    }


async def test_admin_outcome_trace_preserves_missing_evidence(monkeypatch):
    async def fake_get_outcome_trace(**kwargs):
        return _trace(completeness="PARTIAL")

    monkeypatch.setattr(admin_outcomes, "get_outcome_trace", fake_get_outcome_trace)

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/trace",
            params={"tenant_code": "FNB", "include_sections": ["reward"]},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["trace"]["trace_completeness"] == "PARTIAL"
    assert body["trace"]["missing_evidence"][0]["code"] == "NO_SOURCE_EVIDENCE"


async def test_admin_outcome_trace_rejects_malformed_referral_track_id():
    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/outcomes/not-a-uuid/trace",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 422


async def test_admin_outcome_trace_rejects_cross_tenant_operator_jwt(monkeypatch):
    identity = {
        "authenticated": True,
        "role": "FINANCE_ADMIN",
        "tenant_code": "PNP",
        "tenant": "PNP",
        "auth_source": "jwt",
    }

    assert UUID(TRACE_ID)
    with pytest.raises(Exception) as exc_info:
        admin_outcomes._require_operator_identity(identity, "FNB")

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "permission_denied"
