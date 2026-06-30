from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import admin_onboarding
from services.onboarding.onboarding_draft_idempotency_service import (
    evaluate_draft_idempotency,
)

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}
SYSTEM_ADMIN_HEADERS = {"x-api-key": "test-system-admin-key"}
FINANCE_ADMIN_HEADERS = {"x-api-key": "test-finance-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}
PRODUCER_HEADERS = {"x-api-key": "test-fnb-producer-insureco-key"}
DISTRIBUTOR_HEADERS = {"x-api-key": "test-fnb-distributor-insurance-advocate-key"}
CONSUMER_HEADERS = {"x-api-key": "test-fnb-consumer-key"}


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
    [
        FINANCE_ADMIN_HEADERS,
        PARTNER_HEADERS,
        PRODUCER_HEADERS,
        DISTRIBUTOR_HEADERS,
        CONSUMER_HEADERS,
    ],
)
async def test_admin_onboarding_state_rejects_adjacent_roles(headers, monkeypatch):
    def fake_project_onboarding_state(*args, **kwargs):  # pragma: no cover
        raise AssertionError("projection should not be called")

    monkeypatch.setattr(
        admin_onboarding,
        "project_onboarding_state",
        fake_project_onboarding_state,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.get(
            "/admin/onboarding/state",
            params={"external_tenant_ref": "acme-distribution"},
        )

    assert response.status_code == 403
    rendered = json.dumps(response.json()).lower()
    assert "permission_denied" in rendered
    assert "acme-distribution" not in rendered
    assert "tenant_code" not in rendered
    assert "traceback" not in rendered
    assert "sql" not in rendered


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
    assert set(body["onboarding_state"]) == {
        "contract_version",
        "generated_at",
        "scope",
        "sections",
        "readiness",
        "missing_evidence",
        "redactions",
        "guardrails",
        "source_warnings",
    }
    assert set(body["readiness"]) == {
        "contract_version",
        "generated_at",
        "scope",
        "overall_status",
        "categories",
        "summary",
        "guardrails",
        "missing_evidence",
        "source_warnings",
        "redactions",
    }
    assert body["onboarding_state"]["contract_version"] == "onboarding.v1"
    assert body["readiness"]["contract_version"] == "onboarding.v1"
    assert body["onboarding_state"]["scope"]["external_tenant_ref"] == (
        "acme-distribution"
    )
    assert body["readiness"]["scope"]["organisation_ref"] == "org-acme"
    assert body["readiness"]["summary"]["total_count"] == 8
    for category in body["readiness"]["categories"]:
        assert {
            "category",
            "display_label",
            "status",
            "safe_display_status",
            "path",
            "evidence_summary",
            "blockers",
            "next_actions",
            "source_evidence_refs",
            "guardrails",
        }.issubset(category)
        assert category["safe_display_status"]["go_live_enabled"] is False


async def test_admin_onboarding_state_scope_uses_external_references_only(
    monkeypatch,
):
    calls = []

    def fake_project_onboarding_state(evidence, **kwargs):
        calls.append((evidence, kwargs))
        return {
            "contract_version": "onboarding.v1",
            "generated_at": "2026-06-28T00:00:00Z",
            "scope": {
                "external_tenant_ref": evidence["scope"]["external_tenant_ref"],
                "organisation_ref": evidence["scope"]["organisation_ref"],
                "producer_ref": evidence["scope"]["producer_ref"],
                "sponsor_ref": evidence["scope"]["sponsor_ref"],
                "distributor_ref": evidence["scope"]["distributor_ref"],
                "campaign_code": evidence["scope"]["campaign_code"],
                "opportunity_ref": evidence["scope"]["opportunity_ref"],
                "resolved_tenant": {"status": "UNAVAILABLE"},
            },
            "sections": {},
            "readiness": {},
            "missing_evidence": [],
            "redactions": [],
            "guardrails": ["READ_ONLY_PROJECTION", "TENANT_CODE_INTERNAL"],
            "source_warnings": [],
        }

    def fake_aggregate_onboarding_readiness(projection, **kwargs):
        return {
            "contract_version": "onboarding.v1",
            "scope": projection["scope"],
            "overall_status": "GO_LIVE_DISABLED",
            "categories": [],
            "summary": {"total_count": 0},
            "guardrails": ["READ_ONLY_AGGREGATION", "TENANT_CODE_INTERNAL"],
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
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/onboarding/state",
            params={
                "external_tenant_ref": " acme-distribution ",
                "organisation_ref": " org-acme ",
                "producer_ref": " prod-acme ",
                "sponsor_ref": " sponsor-acme ",
                "distributor_ref": " dist-acme ",
                "campaign_code": " camp-acme ",
                "opportunity_ref": " opp-acme ",
                "tenant_code": "INTERNAL-SHOULD-NOT-BE-SCOPE",
            },
        )

    assert response.status_code == 200
    expected_scope = {
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
        "producer_ref": "prod-acme",
        "sponsor_ref": "sponsor-acme",
        "distributor_ref": "dist-acme",
        "campaign_code": "camp-acme",
        "opportunity_ref": "opp-acme",
    }
    assert calls == [({"scope": expected_scope}, {})]
    rendered = json.dumps(response.json())
    assert "INTERNAL-SHOULD-NOT-BE-SCOPE" not in rendered
    assert (
        "tenant_code"
        not in response.json()["onboarding_state"]["scope"]["resolved_tenant"]
    )


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


def _complete_draft_payload(**overrides):
    payload = {
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
        "producer_ref": "prod-acme",
        "sponsor_ref": "sponsor-acme",
        "distributor_ref": "dist-acme",
        "campaign_code": "CAMP-ACME",
        "opportunity_ref": "opp-acme",
        "idempotency_key": "draft-save-key-1",
        "sections": {
            "company": {
                "organisation_name": "Acme Distribution",
                "external_tenant_ref": "acme-distribution",
                "organisation_ref": "org-acme",
                "country": "ZA",
                "organisation_type": "Producer",
                "industry": "Insurance",
                "admin_contact": "ops@example.test",
                "intended_role": "producer_admin",
            },
            "producer_sponsor": {
                "producer_sponsor_name": "Acme Producer",
                "external_tenant_ref": "acme-distribution",
                "producer_ref": "prod-acme",
                "sponsor_ref": "sponsor-acme",
                "organisation_ref": "org-acme",
                "industry": "Insurance",
                "funding_model_intention": "prefunded",
                "admin_contact": "sponsor@example.test",
                "campaign_opportunity_role": "campaign_owner",
            },
            "distributor": {
                "distributor_name": "Acme Broker Network",
                "external_tenant_ref": "acme-distribution",
                "distributor_ref": "dist-acme",
                "organisation_ref": "org-acme",
                "channel_type": "broker",
                "market_country": "ZA",
                "admin_contact": "broker@example.test",
                "distribution_model": "managed_routes",
                "campaign_opportunity_participation": "eligible",
            },
            "member_role": {
                "organisation_ref": "org-acme",
                "external_tenant_ref": "acme-distribution",
                "user_email": "user@example.test",
                "display_name": "Operator User",
                "role_family": "operator",
                "participant_type": "platform_operator",
                "access_scope": "organisation",
                "invite_status": "draft",
            },
            "campaign_opportunity": {
                "organisation_ref": "org-acme",
                "producer_ref": "prod-acme",
                "sponsor_ref": "sponsor-acme",
                "campaign_code": "CAMP-ACME",
                "opportunity_ref": "opp-acme",
                "campaign_name": "Acme Launch",
                "market_country": "ZA",
                "distribution_model": "partner",
                "eligible_distributor_type": "broker",
                "intended_outcome_event": "policy_bound",
                "reward_commission_policy_intention": "commission",
                "funding_model_intention": "prefunded",
                "go_live_target_status": "review",
                "link_code_intent": "campaign_link",
            },
            "webhook_api": {
                "organisation_ref": "org-acme",
                "external_tenant_ref": "acme-distribution",
                "integration_owner_contact": "integration@example.test",
                "api_environment_intention": "sandbox",
                "callback_url_placeholder": "https://example.test/webhooks",
                "selected_webhook_event_categories": ["campaign", "outcome"],
                "intended_authentication_method": "signed_webhook",
                "ip_allowlist_notes": "office egress",
                "payload_format_version": "v1",
                "go_live_readiness_status": "review",
            },
        },
    }
    payload.update(overrides)
    return payload


def _patch_draft_repo(monkeypatch, *, existing_idempotency=None, existing_draft=None):
    calls = {
        "create_draft": [],
        "upsert_draft_section": [],
        "record_validation_result": [],
        "record_idempotency_reference": [],
        "create_audit_link_reference": [],
    }

    async def fake_get_idempotency_reference(**kwargs):
        calls["get_idempotency_reference"] = kwargs
        return existing_idempotency

    async def fake_get_draft_by_ref(draft_ref):
        calls["get_draft_by_ref"] = draft_ref
        return existing_draft

    async def fake_create_draft(**kwargs):
        calls["create_draft"].append(kwargs)
        return {
            "draft_id": "draft-uuid",
            "draft_ref": kwargs["draft_ref"],
            "draft_version": 1,
            "status": kwargs.get("status", "DRAFT_CREATED"),
        }

    async def fake_upsert_draft_section(**kwargs):
        calls["upsert_draft_section"].append(kwargs)
        return kwargs

    async def fake_record_validation_result(**kwargs):
        calls["record_validation_result"].append(kwargs)
        return kwargs

    async def fake_record_idempotency_reference(**kwargs):
        calls["record_idempotency_reference"].append(kwargs)
        return {"idempotency_id": "idem-uuid", **kwargs}

    async def fake_create_audit_link_reference(**kwargs):
        calls["create_audit_link_reference"].append(kwargs)
        return kwargs

    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "get_idempotency_reference",
        fake_get_idempotency_reference,
    )
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "get_draft_by_ref",
        fake_get_draft_by_ref,
    )
    monkeypatch.setattr(admin_onboarding.draft_repo, "create_draft", fake_create_draft)
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "upsert_draft_section",
        fake_upsert_draft_section,
    )
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "record_validation_result",
        fake_record_validation_result,
    )
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "record_idempotency_reference",
        fake_record_idempotency_reference,
    )
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "create_audit_link_reference",
        fake_create_audit_link_reference,
    )
    return calls


def _existing_idempotency_for(payload, *, request_hash=None):
    scope = admin_onboarding._scope_from_payload(payload)
    sections = admin_onboarding._sections_from_payload(payload)
    draft_ref = admin_onboarding._draft_ref(scope)
    decision = evaluate_draft_idempotency(
        idempotency_key=payload["idempotency_key"],
        actor_ref="ADMIN",
        external_tenant_ref=scope["external_tenant_ref"],
        operation_type="ONBOARDING_DRAFT_CREATE",
        request_payload={"scope": scope, "sections": sections, "correlation_id": ""},
        draft_ref=draft_ref,
    )
    fields = decision.repository_fields()
    return {
        **fields,
        "request_hash": request_hash or fields["request_hash"],
        "result_status": "SUCCESS",
        "response_hash": "prior-response-hash",
    }


async def test_admin_onboarding_draft_save_requires_auth(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/admin/onboarding/drafts", json=_complete_draft_payload()
        )

    assert response.status_code == 401
    assert calls["create_draft"] == []


async def test_admin_onboarding_draft_save_rejects_adjacent_role(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    async with AsyncClient(
        app=app, base_url="http://test", headers=FINANCE_ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts", json=_complete_draft_payload()
        )

    assert response.status_code == 403
    assert calls["create_draft"] == []


async def test_admin_onboarding_draft_save_persists_draft_intent_only(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)
    payload = _complete_draft_payload()

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/drafts", json=payload)

    assert response.status_code == 200
    body = response.json()
    rendered = json.dumps(body)
    assert body["status"] == "saved"
    assert body["draft_ref"].startswith("draft_")
    assert body["draft_status"] == "DRAFT_CREATED"
    assert body["idempotency_status"] == "NEW_REQUEST"
    assert body["no_live_action_confirmed"] is True
    assert body["readiness_preview"]["overall_status"] == "GO_LIVE_DISABLED"
    assert calls["create_draft"][0]["external_tenant_ref"] == "acme-distribution"
    assert calls["create_draft"][0]["created_by_role"] == "ADMIN"
    assert calls["upsert_draft_section"]
    assert calls["record_validation_result"]
    assert calls["record_idempotency_reference"]
    assert calls["create_audit_link_reference"]
    assert calls["record_idempotency_reference"][0]["idempotency_key_hash"]
    audit_link = calls["create_audit_link_reference"][0]
    evidence_summary = audit_link["evidence_summary"]
    assert audit_link["action_type"] == "ONBOARDING_DRAFT_CREATE"
    assert audit_link["action_status"] == "SUCCESS"
    assert audit_link["actor_ref"] == "ADMIN"
    assert audit_link["actor_role"] == "ADMIN"
    assert audit_link["event_ref"] is None
    assert audit_link["idempotency_id"] == "idem-uuid"
    assert audit_link["before_state_hash"]
    assert audit_link["after_state_hash"]
    assert sorted(audit_link["changed_sections"]) == sorted(payload["sections"])
    assert evidence_summary["external_scope"] == {
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
        "producer_ref": "prod-acme",
        "sponsor_ref": "sponsor-acme",
        "distributor_ref": "dist-acme",
        "campaign_code": "CAMP-ACME",
        "opportunity_ref": "opp-acme",
    }
    assert evidence_summary["dispatch"] == {
        "event_dispatched": False,
        "webhook_dispatched": False,
        "event_ref": None,
    }
    assert "draft-save-key-1" not in rendered
    assert "tenant_code" not in body["validation_result"]["validated_scope"]
    assert "create_tenant" not in rendered
    assert "send_invite" not in rendered
    assert "deliver_webhook" not in rendered
    assert "wallet" not in rendered.lower()


async def test_admin_onboarding_draft_save_replays_same_idempotency_payload(
    monkeypatch,
):
    payload = _complete_draft_payload()
    calls = _patch_draft_repo(
        monkeypatch,
        existing_idempotency=_existing_idempotency_for(payload),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/drafts", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "replayed"
    assert body["idempotency_status"] == "REPLAY_SAME_PAYLOAD"
    assert calls["create_draft"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []


async def test_admin_onboarding_draft_save_conflicts_on_different_payload(monkeypatch):
    payload = _complete_draft_payload()
    calls = _patch_draft_repo(
        monkeypatch,
        existing_idempotency=_existing_idempotency_for(
            payload, request_hash="different"
        ),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/drafts", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert calls["create_draft"] == []


async def test_admin_onboarding_draft_save_duplicate_draft_is_safe(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft={"draft_ref": "existing-draft", "status": "DRAFT_CREATED"},
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts", json=_complete_draft_payload()
        )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "DUPLICATE_DRAFT"
    assert calls["create_draft"] == []


async def test_admin_onboarding_draft_save_rejects_user_facing_tenant_code(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)
    payload = _complete_draft_payload(tenant_code="INTERNAL_ACME")

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/drafts", json=payload)

    assert response.status_code == 422
    rendered = json.dumps(response.json())
    assert response.json()["detail"]["code"] == "UNSAFE_OPERATION_ATTEMPTED"
    assert "INTERNAL_ACME" not in rendered
    assert calls["create_draft"] == []


async def test_admin_onboarding_draft_save_rejects_secret_payload(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)
    payload = _complete_draft_payload()
    payload["sections"]["webhook_api"]["api_key"] = "SECRET-API-KEY"
    payload["sections"]["webhook_api"]["client_secret"] = "SECRET-CLIENT"

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/drafts", json=payload)

    rendered = json.dumps(response.json())
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSAFE_OPERATION_ATTEMPTED"
    assert "SECRET-API-KEY" not in rendered
    assert "SECRET-CLIENT" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered
    assert calls["create_draft"] == []


async def test_admin_onboarding_draft_save_rejects_live_action_payload(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)
    payload = _complete_draft_payload()
    payload["sections"]["campaign_opportunity"]["publish_campaign"] = True
    payload["sections"]["webhook_api"]["deliver_webhook"] = True

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/drafts", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSAFE_OPERATION_ATTEMPTED"
    assert calls["create_draft"] == []
    assert calls["record_validation_result"] == []
