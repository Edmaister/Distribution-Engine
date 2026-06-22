from __future__ import annotations

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import operator_control_plane
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
        "redactions": [{"field": "referrer_ucn"}],
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
        "totals": {"obligation_total": "125.00"},
        "totals_by_category": {},
        "items": [],
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
        "redactions": [{"field": "provider_response"}],
        "generated_at": "2026-06-22T00:00:00Z",
    }


async def test_system_admin_can_load_operator_control_plane_shell(monkeypatch):
    trace_calls = []
    projection_calls = []

    async def fake_get_outcome_trace(**kwargs):
        trace_calls.append(kwargs)
        return _trace()

    async def fake_get_outcome_liability_projection(**kwargs):
        projection_calls.append(kwargs)
        return _projection()

    monkeypatch.setattr(
        operator_control_plane, "get_outcome_trace", fake_get_outcome_trace
    )
    monkeypatch.setattr(
        operator_control_plane,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={"tenant_code": "fnb"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["tenant_code"] == "FNB"
    assert body["requested_sections"] == operator_control_plane.CONTRACTED_SECTIONS
    assert body["sections"]["outcome_trace"]["status"] == "ok"
    assert body["sections"]["funding_liability"]["status"] == "ok"
    assert body["sections"]["campaign_readiness"]["status"] == "not_implemented"
    assert "campaign_readiness" in body["unavailable_sections"]
    assert body["permission_denied_sections"] == []
    assert {"field": "referrer_ucn"} in body["redactions"]
    assert {"field": "provider_response"} in body["redactions"]
    assert body["guardrail"].startswith("Read-only aggregate")
    assert trace_calls[0]["tenant_code"] == "FNB"
    assert trace_calls[0]["referral_track_id"] == TRACE_ID
    assert projection_calls[0]["tenant_code"] == "FNB"


async def test_operator_control_plane_can_return_ok_for_implemented_sections_only(
    monkeypatch,
):
    async def fake_get_outcome_trace(**kwargs):
        return _trace()

    async def fake_get_outcome_liability_projection(**kwargs):
        return _projection()

    monkeypatch.setattr(
        operator_control_plane, "get_outcome_trace", fake_get_outcome_trace
    )
    monkeypatch.setattr(
        operator_control_plane,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params=[
                ("tenant_code", "FNB"),
                ("sections", "outcome_trace"),
                ("sections", "funding_liability"),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body["sections"]) == {"outcome_trace", "funding_liability"}
    assert body["unavailable_sections"] == []


async def test_operator_control_plane_preserves_missing_evidence(monkeypatch):
    async def fake_get_outcome_trace(**kwargs):
        return _trace(completeness="PARTIAL")

    monkeypatch.setattr(
        operator_control_plane, "get_outcome_trace", fake_get_outcome_trace
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={"tenant_code": "FNB", "sections": "outcome_trace"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["sections"]["outcome_trace"]["status"] == "missing_evidence"
    assert body["sections"]["outcome_trace"]["missing_evidence"][0]["code"] == (
        "NO_SOURCE_EVIDENCE"
    )


async def test_operator_control_plane_returns_section_permission_denied(monkeypatch):
    liability_called = False

    async def fake_get_outcome_trace(**kwargs):
        return _trace()

    async def fake_get_outcome_liability_projection(**kwargs):
        nonlocal liability_called
        liability_called = True
        return _projection()

    monkeypatch.setattr(
        operator_control_plane, "get_outcome_trace", fake_get_outcome_trace
    )
    monkeypatch.setattr(
        operator_control_plane,
        "get_outcome_liability_projection",
        fake_get_outcome_liability_projection,
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"x-api-key": "test-distribution-admin-key"},
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params=[
                ("tenant_code", "FNB"),
                ("sections", "outcome_trace"),
                ("sections", "funding_liability"),
            ],
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["sections"]["outcome_trace"]["status"] == "ok"
    assert body["sections"]["funding_liability"]["status"] == "permission_denied"
    assert body["permission_denied_sections"] == ["funding_liability"]
    assert liability_called is False


async def test_operator_control_plane_returns_401_without_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={"tenant_code": "FNB"},
        )

    assert response.status_code == 401


async def test_operator_control_plane_rejects_non_operator_identity(monkeypatch):
    async def fake_get_outcome_trace(**kwargs):  # pragma: no cover - should not run
        raise AssertionError("service should not be called")

    monkeypatch.setattr(
        operator_control_plane, "get_outcome_trace", fake_get_outcome_trace
    )

    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"x-api-key": "test-partner-key"},
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={"tenant_code": "FNB", "sections": "outcome_trace"},
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "permission_denied"


async def test_operator_control_plane_returns_safe_validation_error():
    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={"tenant_code": "FNB", "sections": "raw_payload"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "Unsupported operator control-plane section: raw_payload",
    }


async def test_operator_control_plane_returns_safe_not_found_section(monkeypatch):
    async def fake_get_outcome_trace(**kwargs):
        raise OutcomeTraceNotFound("missing")

    monkeypatch.setattr(
        operator_control_plane, "get_outcome_trace", fake_get_outcome_trace
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={"tenant_code": "FNB", "sections": "outcome_trace"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["sections"]["outcome_trace"]["status"] == "unavailable"
    assert body["sections"]["outcome_trace"]["error"] == {
        "code": "not_found",
        "message": "outcome_trace source evidence was not found for this tenant.",
        "retryable": False,
    }
