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


def _projection(*, completeness: str = "COMPLETE") -> dict:
    return {
        "projection_type": "OUTCOME_LIABILITY",
        "tenant_code": "FNB",
        "lookup": {"type": "REFERRAL_TRACK_ID", "value": TRACE_ID},
        "trace_id": f"outcome:referral_track_id:{TRACE_ID}",
        "trace_completeness": completeness,
        "liability_completeness": completeness,
        "totals": {
            "obligation_total": "125.00",
            "reserved_total": "100.00",
            "released_total": "0.00",
            "fulfilled_total": "125.00",
            "settled_total": "100.00",
            "reversed_total": "0.00",
            "failed_total": "0.00",
            "disputed_total": "0.00",
        },
        "totals_by_category": {},
        "items": [
            {
                "source_family": "reward",
                "source": "rewards",
                "source_id": "reward-1",
                "liability_category": "REFERRER_REWARD",
                "derived_state": "CALCULATED",
                "amount": "100.00",
                "currency": "ZAR",
                "source_status": "APPLIED",
                "join_confidence": "MEDIUM",
                "evidence": {"reward_id": "reward-1", "status": "APPLIED"},
            }
        ],
        "support_trace": {"audit_reference_count": 0},
        "missing_evidence": (
            []
            if completeness == "COMPLETE"
            else [
                {
                    "section": "funding",
                    "code": "JOIN_AMBIGUOUS",
                    "severity": "WARNING",
                    "source": "funding_reservations",
                    "message": "Funding join is weak.",
                }
            ]
        ),
        "source_warnings": [],
        "redactions": [{"field": "referrer_ucn"}],
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


async def test_system_admin_can_fetch_outcome_liability_projection(monkeypatch):
    calls = []

    async def fake_get_outcome_liability_projection(**kwargs):
        calls.append(kwargs)
        return _projection()

    monkeypatch.setattr(
        admin_outcomes,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/liability",
            params={"tenant_code": "fnb"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["projection"]["projection_type"] == "OUTCOME_LIABILITY"
    assert body["projection"]["tenant_code"] == "FNB"
    assert body["projection"]["liability_completeness"] == "COMPLETE"
    assert body["projection"]["redactions"] == [{"field": "referrer_ucn"}]
    assert body["guardrail"].startswith("Read-only operator liability projection")
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
async def test_admin_outcome_liability_allows_operator_admin_roles(
    monkeypatch, headers
):
    async def fake_get_outcome_liability_projection(**kwargs):
        return _projection()

    monkeypatch.setattr(
        admin_outcomes,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/liability",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200


async def test_admin_outcome_liability_returns_401_without_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/liability",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 401


async def test_admin_outcome_liability_rejects_non_operator_identity(monkeypatch):
    async def fake_get_outcome_liability_projection(
        **kwargs,
    ):  # pragma: no cover - should not run
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        admin_outcomes,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers={"x-api-key": "test-partner-key"}
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/liability",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_admin_outcome_liability_returns_404_for_missing_outcome(monkeypatch):
    async def fake_get_outcome_liability_projection(**kwargs):
        raise OutcomeTraceNotFound("missing")

    monkeypatch.setattr(
        admin_outcomes,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/liability",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "code": "outcome_not_found",
        "message": (
            "Outcome liability projection was not found for the requested tenant."
        ),
    }


async def test_admin_outcome_liability_returns_safe_validation_error(monkeypatch):
    async def fake_get_outcome_liability_projection(**kwargs):
        raise ValueError("tenant_code is required")

    monkeypatch.setattr(
        admin_outcomes,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/liability",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "tenant_code is required",
    }


async def test_admin_outcome_liability_preserves_missing_evidence(monkeypatch):
    async def fake_get_outcome_liability_projection(**kwargs):
        return _projection(completeness="PARTIAL")

    monkeypatch.setattr(
        admin_outcomes,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/admin/outcomes/{TRACE_ID}/liability",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["projection"]["liability_completeness"] == "PARTIAL"
    assert body["projection"]["missing_evidence"][0]["code"] == "JOIN_AMBIGUOUS"
