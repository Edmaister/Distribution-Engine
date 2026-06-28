from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import admin_onboarding

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}
SYSTEM_ADMIN_HEADERS = {"x-api-key": "test-system-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}


async def test_admin_onboarding_state_returns_401_without_credentials(monkeypatch):
    def fake_project_onboarding_state(*args, **kwargs):  # pragma: no cover
        raise AssertionError("projection should not be called")

    monkeypatch.setattr(
        admin_onboarding,
        "project_onboarding_state",
        fake_project_onboarding_state,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/onboarding/state")

    assert response.status_code == 401


async def test_admin_onboarding_state_rejects_non_admin_identity(monkeypatch):
    def fake_project_onboarding_state(*args, **kwargs):  # pragma: no cover
        raise AssertionError("projection should not be called")

    monkeypatch.setattr(
        admin_onboarding,
        "project_onboarding_state",
        fake_project_onboarding_state,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=PARTNER_HEADERS
    ) as client:
        response = await client.get("/admin/onboarding/state")

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "code": "permission_denied",
        "message": "API key is not authorised for onboarding state.",
    }


@pytest.mark.parametrize(
    "headers",
    [ADMIN_HEADERS, DISTRIBUTION_ADMIN_HEADERS, SYSTEM_ADMIN_HEADERS],
)
async def test_admin_onboarding_state_returns_projection_and_readiness(headers):
    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.get(
            "/admin/onboarding/state",
            params={
                "external_tenant_ref": "acme-distribution",
                "organisation_ref": "org-acme",
                "producer_ref": "prod-acme",
                "sponsor_ref": "sponsor-acme",
                "distributor_ref": "dist-acme",
                "campaign_code": "CAMP-ACME",
                "opportunity_ref": "opp-acme",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body) == {"status", "onboarding_state", "readiness", "guardrail"}
    assert body["guardrail"].startswith("Read-only admin onboarding state")
    assert "does not create or update" in body["guardrail"]
    assert body["onboarding_state"]["contract_version"] == "onboarding.v1"
    assert body["readiness"]["contract_version"] == "onboarding.v1"
    assert body["onboarding_state"]["scope"]["external_tenant_ref"] == (
        "acme-distribution"
    )
    assert body["readiness"]["scope"]["organisation_ref"] == "org-acme"
    assert body["readiness"]["summary"]["total_count"] == 8


async def test_admin_onboarding_state_marks_missing_evidence_explicitly():
    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get("/admin/onboarding/state")

    assert response.status_code == 200
    body = response.json()
    state = body["onboarding_state"]
    readiness = body["readiness"]
    assert any(
        item["code"] == "NO_RESOLVED_TENANT" for item in state["missing_evidence"]
    )
    assert any(
        item["code"] == "NO_BACKEND_SOURCE" for item in state["missing_evidence"]
    )
    assert readiness["summary"]["missing_evidence_count"] == 6
    assert readiness["overall_status"] == "GO_LIVE_DISABLED"


async def test_admin_onboarding_state_unknown_or_unresolved_refs_are_safe():
    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/onboarding/state",
            params={"external_tenant_ref": "unknown-demo-tenant"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["onboarding_state"]["scope"]["external_tenant_ref"] == (
        "unknown-demo-tenant"
    )
    assert body["readiness"]["summary"]["missing_evidence_count"] == 6
    assert body["readiness"]["categories"][0]["status"] == "MISSING_EVIDENCE"
    assert "traceback" not in json.dumps(body).lower()
    assert "sql" not in json.dumps(body).lower()


async def test_admin_onboarding_state_is_redaction_safe():
    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/onboarding/state",
            params={
                "external_tenant_ref": "acme-distribution",
                "organisation_ref": "org-acme",
            },
        )

    assert response.status_code == 200
    rendered = json.dumps(response.json())
    assert (
        "tenant_code"
        not in response.json()["onboarding_state"]["scope"]["resolved_tenant"]
    )
    assert "tenant_code" not in response.json()["readiness"]["scope"]["resolved_tenant"]
    assert "secret-value" not in rendered.lower()
    assert "api-key-value" not in rendered.lower()
    assert "client-secret-value" not in rendered.lower()
    assert "provider-payload-value" not in rendered.lower()
    assert "raw-audit-value" not in rendered.lower()
    assert "wallet-account-value" not in rendered.lower()
    assert "settlement-internal-value" not in rendered.lower()
    assert "fulfilment-internal-value" not in rendered.lower()
    assert "retry-internal-value" not in rendered.lower()
    assert "private-ucn-value" not in rendered.lower()


async def test_admin_onboarding_state_calls_only_read_only_helpers(monkeypatch):
    calls = []

    def fake_project_onboarding_state(evidence, **kwargs):
        calls.append(("project", evidence, kwargs))
        return {
            "contract_version": "onboarding.v1",
            "generated_at": "2026-06-28T00:00:00Z",
            "scope": {
                "external_tenant_ref": evidence["scope"]["external_tenant_ref"],
                "organisation_ref": None,
                "producer_ref": None,
                "sponsor_ref": None,
                "distributor_ref": None,
                "campaign_code": None,
                "opportunity_ref": None,
                "resolved_tenant": {"status": "UNAVAILABLE"},
            },
            "sections": {},
            "readiness": {},
            "missing_evidence": [],
            "redactions": [],
            "guardrails": ["READ_ONLY_PROJECTION"],
            "source_warnings": [],
        }

    def fake_aggregate_onboarding_readiness(projection, **kwargs):
        calls.append(("aggregate", projection, kwargs))
        return {
            "contract_version": "onboarding.v1",
            "scope": projection["scope"],
            "overall_status": "GO_LIVE_DISABLED",
            "categories": [],
            "summary": {"total_count": 0},
            "guardrails": ["READ_ONLY_AGGREGATION"],
            "missing_evidence": [],
            "source_warnings": [],
            "redactions": [],
        }

    monkeypatch.setattr(
        admin_onboarding,
        "project_onboarding_state",
        fake_project_onboarding_state,
    )
    monkeypatch.setattr(
        admin_onboarding,
        "aggregate_onboarding_readiness",
        fake_aggregate_onboarding_readiness,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/onboarding/state",
            params={"external_tenant_ref": "acme-distribution"},
        )

    assert response.status_code == 200
    assert [call[0] for call in calls] == ["project", "aggregate"]
    assert calls[0][1] == {"scope": {"external_tenant_ref": "acme-distribution"}}
    assert "create" not in response.json()["readiness"]
    assert "update" not in response.json()["readiness"]
    assert "activate" not in response.json()["readiness"]
