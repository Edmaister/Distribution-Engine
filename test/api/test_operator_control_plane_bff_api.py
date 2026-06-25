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


def _campaign_readiness(
    *,
    readiness: str = "READY",
    blockers: list[dict] | None = None,
    warnings: list[dict] | None = None,
    unknowns: list[dict] | None = None,
) -> dict:
    return {
        "tenant_code": "FNB",
        "campaign_code": "CAMP001",
        "opportunity_id": None,
        "operation": "CONTROL_PLANE_VIEW",
        "canonical_lifecycle": "ACTIVE",
        "readiness": readiness,
        "can_proceed": readiness in {"READY", "READY_WITH_WARNINGS"},
        "blockers": blockers or [],
        "warnings": warnings or [],
        "unknowns": unknowns or [],
        "evidence": {"campaign": {"campaign_code": "CAMP001"}},
        "evaluated_at": "2026-06-25T00:00:00Z",
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
    assert body["sections"]["campaign_readiness"]["status"] == "unavailable"
    assert "campaign_readiness" in body["unavailable_sections"]
    assert body["permission_denied_sections"] == []
    assert {"field": "referrer_ucn"} in body["redactions"]
    assert {"field": "provider_response"} in body["redactions"]
    assert body["guardrail"].startswith("Read-only aggregate")
    assert trace_calls[0]["tenant_code"] == "FNB"
    assert trace_calls[0]["referral_track_id"] == TRACE_ID
    assert projection_calls[0]["tenant_code"] == "FNB"


async def test_operator_control_plane_loads_campaign_readiness_section(monkeypatch):
    calls = []

    async def fake_get_campaign_readiness(**kwargs):
        calls.append(kwargs)
        return _campaign_readiness()

    monkeypatch.setattr(
        operator_control_plane,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={
                "tenant_code": "fnb",
                "sections": "campaign_readiness",
                "campaign_code": "camp001",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["sections"]["campaign_readiness"]["status"] == "ok"
    assert body["sections"]["campaign_readiness"]["data"]["readiness"] == "READY"
    assert body["unavailable_sections"] == []
    assert calls == [
        {
            "tenant_code": "FNB",
            "campaign_code": "camp001",
            "operation": "CONTROL_PLANE_VIEW",
            "opportunity_id": None,
            "include_evidence": True,
        }
    ]


async def test_operator_control_plane_campaign_readiness_preserves_blockers(
    monkeypatch,
):
    async def fake_get_campaign_readiness(**kwargs):
        return _campaign_readiness(
            readiness="NOT_READY",
            blockers=[
                {
                    "code": "CAMPAIGN_INACTIVE",
                    "severity": "BLOCKER",
                    "source": "marketing_campaigns",
                    "message": "Campaign definition is inactive.",
                }
            ],
        )

    monkeypatch.setattr(
        operator_control_plane,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={
                "tenant_code": "FNB",
                "sections": "campaign_readiness",
                "campaign_code": "CAMP001",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    section = body["sections"]["campaign_readiness"]
    assert section["status"] == "missing_evidence"
    assert section["missing_evidence"][0]["code"] == "CAMPAIGN_INACTIVE"


async def test_operator_control_plane_campaign_readiness_requires_campaign_code(
    monkeypatch,
):
    called = False

    async def fake_get_campaign_readiness(**kwargs):
        nonlocal called
        called = True
        return _campaign_readiness()

    monkeypatch.setattr(
        operator_control_plane,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={"tenant_code": "FNB", "sections": "campaign_readiness"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["sections"]["campaign_readiness"]["error"] == {
        "code": "validation_error",
        "message": "campaign_code is required for campaign_readiness.",
        "retryable": False,
    }
    assert called is False


async def test_operator_control_plane_campaign_readiness_handles_invalid_operation(
    monkeypatch,
):
    async def fake_get_campaign_readiness(**kwargs):
        raise ValueError("Unsupported campaign readiness operation: DO_SOMETHING")

    monkeypatch.setattr(
        operator_control_plane,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={
                "tenant_code": "FNB",
                "sections": "campaign_readiness",
                "campaign_code": "CAMP001",
                "campaign_operation": "DO_SOMETHING",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["sections"]["campaign_readiness"]["error"] == {
        "code": "validation_error",
        "message": "Unsupported campaign readiness operation: DO_SOMETHING",
        "retryable": False,
    }


@pytest.mark.parametrize("code", ["CAMPAIGN_NOT_FOUND", "TENANT_MISMATCH"])
async def test_operator_control_plane_campaign_readiness_not_found_blockers(
    monkeypatch, code
):
    async def fake_get_campaign_readiness(**kwargs):
        return _campaign_readiness(
            readiness="NOT_READY",
            blockers=[
                {
                    "code": code,
                    "severity": "BLOCKER",
                    "source": "marketing_campaigns",
                    "message": "Not accessible.",
                }
            ],
        )

    monkeypatch.setattr(
        operator_control_plane,
        "get_campaign_readiness",
        fake_get_campaign_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            f"/v1/experience/operator-control-plane/outcomes/{TRACE_ID}",
            params={
                "tenant_code": "FNB",
                "sections": "campaign_readiness",
                "campaign_code": "CAMP001",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["sections"]["campaign_readiness"]["error"] == {
        "code": "not_found",
        "message": (
            "campaign_readiness source evidence was not found for this tenant."
        ),
        "retryable": False,
    }


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
