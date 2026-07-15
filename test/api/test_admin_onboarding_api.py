from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from apps.api.main import app
from apps.api.routers import admin_onboarding
from services.onboarding import onboarding_review_decision_service as review_service
from services.onboarding import onboarding_submit_for_review_service as submit_service
from services.onboarding.onboarding_draft_idempotency_service import (
    evaluate_draft_idempotency,
)
from services.onboarding.onboarding_draft_repository import StaleDraftVersionError

pytestmark = pytest.mark.asyncio

ADMIN_HEADERS = {"x-api-key": "test-admin-key"}
DISTRIBUTION_ADMIN_HEADERS = {"x-api-key": "test-distribution-admin-key"}
SYSTEM_ADMIN_HEADERS = {"x-api-key": "test-system-admin-key"}
FINANCE_ADMIN_HEADERS = {"x-api-key": "test-finance-admin-key"}
PARTNER_HEADERS = {"x-api-key": "test-partner-key"}
PRODUCER_HEADERS = {"x-api-key": "test-fnb-producer-insureco-key"}
DISTRIBUTOR_HEADERS = {"x-api-key": "test-fnb-distributor-insurance-advocate-key"}
CONSUMER_HEADERS = {"x-api-key": "test-fnb-consumer-key"}

ADJACENT_ROLE_HEADERS = [
    FINANCE_ADMIN_HEADERS,
    PARTNER_HEADERS,
    PRODUCER_HEADERS,
    DISTRIBUTOR_HEADERS,
    CONSUMER_HEADERS,
]

RAW_LEAK_TERMS = (
    "INTERNAL_ACME",
    "INTERNAL-ACME",
    "SECRET-API-KEY",
    "SECRET-CLIENT",
    "ACCESS-TOKEN",
    "SIGNING-SECRET",
    "PRIVATE-KEY",
    "PROVIDER-PAYLOAD",
    "AUDIT-PAYLOAD",
    "RAW-AUDIT",
    "DELIVERY-STATE",
    "funding-value",
    "wallet-internal",
    "settlement-value",
    "fulfilment-value",
    "retry-value",
    "money-value",
    "api_key",
    "client_secret",
    "access_token",
    "signing_secret",
    "private_key",
    "provider_payload",
    "audit_payload",
    "raw_audit_payload",
    "webhook_delivery_state",
    "funding_internal",
    "wallet_internal",
    "settlement_internal",
    "fulfilment_internal",
    "money_movement_detail",
    "traceback",
    "sql",
)


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


def _patch_draft_repo(
    monkeypatch,
    *,
    existing_idempotency=None,
    existing_draft=None,
    draft_list=None,
    draft_sections=None,
    stale_update=False,
):
    calls = {
        "create_draft": [],
        "upsert_draft_section": [],
        "record_validation_result": [],
        "record_idempotency_reference": [],
        "create_audit_link_reference": [],
        "get_draft_sections": [],
        "list_drafts": [],
        "update_draft_metadata_or_status": [],
    }

    async def fake_get_idempotency_reference(**kwargs):
        calls["get_idempotency_reference"] = kwargs
        return existing_idempotency

    async def fake_get_draft_by_ref(draft_ref):
        calls["get_draft_by_ref"] = draft_ref
        return existing_draft

    async def fake_get_draft_sections(draft_id):
        calls["get_draft_sections"].append(draft_id)
        return list(draft_sections or [])

    async def fake_list_drafts(**kwargs):
        calls["list_drafts"].append(kwargs)
        return list(draft_list or [])

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
        return {
            "audit_link_id": "audit-link-uuid",
            **kwargs,
        }

    async def fake_update_draft_metadata_or_status(**kwargs):
        calls["update_draft_metadata_or_status"].append(kwargs)
        if stale_update:
            raise StaleDraftVersionError("stale")
        return {
            **(existing_draft or {}),
            "draft_version": int((existing_draft or {}).get("draft_version") or 1) + 1,
            "status": kwargs.get("status"),
        }

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
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "get_draft_sections",
        fake_get_draft_sections,
    )
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "list_drafts",
        fake_list_drafts,
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
    monkeypatch.setattr(
        admin_onboarding.draft_repo,
        "update_draft_metadata_or_status",
        fake_update_draft_metadata_or_status,
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


def _saved_draft(**overrides):
    draft = {
        "draft_id": "draft-uuid",
        "draft_ref": "draft-submit-1",
        "draft_version": 2,
        "status": "DRAFT_UPDATED",
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
        "producer_ref": "prod-acme",
        "sponsor_ref": "sponsor-acme",
        "distributor_ref": "dist-acme",
        "campaign_code": "CAMP-ACME",
        "opportunity_ref": "opp-acme",
        "tenant_code": "INTERNAL-ACME",
    }
    draft.update(overrides)
    return draft


def _saved_draft_sections(payload=None):
    source = payload or _complete_draft_payload()
    return [
        {
            "draft_id": "draft-uuid",
            "section_key": section_key,
            "section_payload": section_payload,
        }
        for section_key, section_payload in source["sections"].items()
    ]


def _submit_payload(**overrides):
    payload = {
        "expected_version": 2,
        "idempotency_key": "submit-review-key-1",
        "correlation_id": "corr-submit-1",
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
    }
    payload.update(overrides)
    return payload


def _review_payload(**overrides):
    payload = {
        "expected_version": 2,
        "idempotency_key": "review-decision-key-1",
        "correlation_id": "corr-review-1",
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
        "review_outcome": review_service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW,
        "reason_category": "OPERATOR_REVIEW",
        "reason": "Evidence is complete enough for internal review.",
    }
    payload.update(overrides)
    return payload


def _existing_submit_idempotency_for(payload, *, request_hash=None):
    validation = admin_onboarding.validate_onboarding_draft(
        {
            "scope": admin_onboarding._scope_from_draft(_saved_draft()),
            "sections": {
                row["section_key"]: row["section_payload"]
                for row in _saved_draft_sections()
            },
        },
        actor_context={"actor_ref": "ADMIN", "actor_role": "ADMIN"},
    )
    request_payload = submit_service.build_submit_for_review_request_payload(
        draft_ref="draft-submit-1",
        expected_draft_version=payload["expected_version"],
        validation=validation,
    )
    decision = submit_service.evaluate_draft_idempotency(
        idempotency_key=payload["idempotency_key"],
        actor_ref="ADMIN",
        external_tenant_ref="acme-distribution",
        operation_type=submit_service.OPERATION_SUBMIT_FOR_REVIEW,
        request_payload=request_payload,
        draft_ref="draft-submit-1",
    )
    fields = decision.repository_fields()
    return {
        **fields,
        "request_hash": request_hash or fields["request_hash"],
        "result_status": "SUCCESS",
        "response_hash": "prior-submit-response-hash",
    }


def _existing_review_idempotency_for(payload, *, request_hash=None):
    validation = admin_onboarding.validate_onboarding_draft(
        {
            "scope": admin_onboarding._scope_from_draft(
                _saved_draft(status="READY_FOR_REVIEW")
            ),
            "sections": {
                row["section_key"]: row["section_payload"]
                for row in _saved_draft_sections()
            },
        },
        actor_context={"actor_ref": "ADMIN", "actor_role": "ADMIN"},
    )
    request_payload = review_service.build_review_decision_request_payload(
        draft_ref="draft-submit-1",
        expected_draft_version=payload["expected_version"],
        review_outcome=payload["review_outcome"],
        reason_category=payload["reason_category"],
        reason=payload["reason"],
        validation=validation,
        target_status=review_service.target_status_for_review_outcome(
            payload["review_outcome"]
        ),
    )
    decision = review_service.evaluate_draft_idempotency(
        idempotency_key=payload["idempotency_key"],
        actor_ref="ADMIN",
        external_tenant_ref="acme-distribution",
        operation_type=review_service.OPERATION_REVIEW_DECISION,
        request_payload=request_payload,
        draft_ref="draft-submit-1",
    )
    fields = decision.repository_fields()
    return {
        **fields,
        "request_hash": request_hash or fields["request_hash"],
        "result_status": "SUCCESS",
        "response_hash": "prior-review-response-hash",
    }


def _assert_no_draft_repo_persistence(calls):
    assert calls["create_draft"] == []
    assert calls["upsert_draft_section"] == []
    assert calls["record_validation_result"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    assert calls["get_draft_sections"] == []
    assert calls["update_draft_metadata_or_status"] == []
    assert "get_idempotency_reference" not in calls
    assert "get_draft_by_ref" not in calls


def _assert_no_raw_leaks(payload):
    rendered = json.dumps(payload)
    rendered_lower = rendered.lower()
    for term in RAW_LEAK_TERMS:
        assert term.lower() not in rendered_lower
    assert '"tenant_code":' not in rendered_lower


def _assert_submit_did_not_invoke_live_actions(calls):
    assert calls["create_draft"] == []
    assert calls["upsert_draft_section"] == []
    assert calls["record_validation_result"] == []
    assert len(calls["update_draft_metadata_or_status"]) <= 1
    assert len(calls["record_idempotency_reference"]) <= 1
    assert len(calls["create_audit_link_reference"]) <= 1


def _assert_review_route_helpers_not_called(calls, helper_calls):
    _assert_no_draft_repo_persistence(calls)
    assert helper_calls == []


def _patch_review_flow_helpers_to_fail(monkeypatch):
    calls = []

    def fail_project(*args, **kwargs):  # pragma: no cover
        calls.append("project")
        raise AssertionError("projection should not be called")

    def fail_aggregate(*args, **kwargs):  # pragma: no cover
        calls.append("aggregate")
        raise AssertionError("readiness aggregation should not be called")

    def fail_validation(*args, **kwargs):  # pragma: no cover
        calls.append("validate")
        raise AssertionError("validation should not be called")

    async def fail_submit(*args, **kwargs):  # pragma: no cover
        calls.append("submit")
        raise AssertionError("submit transition should not be called")

    async def fail_review_decision(*args, **kwargs):  # pragma: no cover
        calls.append("review_decision")
        raise AssertionError("review decision should not be called")

    monkeypatch.setattr(admin_onboarding, "project_onboarding_state", fail_project)
    monkeypatch.setattr(
        admin_onboarding,
        "aggregate_onboarding_readiness",
        fail_aggregate,
    )
    monkeypatch.setattr(admin_onboarding, "validate_onboarding_draft", fail_validation)
    monkeypatch.setattr(
        admin_onboarding,
        "submit_onboarding_draft_for_review",
        fail_submit,
    )
    monkeypatch.setattr(
        admin_onboarding,
        "record_onboarding_draft_review_decision",
        fail_review_decision,
    )
    return calls


def _review_flow_route_cases():
    return [
        (
            "state",
            "GET",
            "/admin/onboarding/state",
            {"external_tenant_ref": "acme-distribution"},
            None,
        ),
        (
            "validate",
            "POST",
            "/admin/onboarding/validate",
            None,
            _complete_draft_payload(),
        ),
        (
            "draft_save",
            "POST",
            "/admin/onboarding/drafts",
            None,
            _complete_draft_payload(),
        ),
        (
            "submit_for_review",
            "POST",
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            None,
            _submit_payload(),
        ),
        (
            "review_decision",
            "POST",
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            None,
            _review_payload(),
        ),
    ]


async def _call_review_flow_route(client, method, path, params, body):
    if method == "GET":
        return await client.get(path, params=params)
    return await client.post(path, json=body)


@pytest.mark.parametrize(
    "route_name,method,path,params,body",
    _review_flow_route_cases(),
)
async def test_review_flow_routes_reject_unauthenticated_before_helpers(
    route_name,
    method,
    path,
    params,
    body,
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch, existing_draft=_saved_draft())
    helper_calls = _patch_review_flow_helpers_to_fail(monkeypatch)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await _call_review_flow_route(client, method, path, params, body)

    assert response.status_code == 401, route_name
    _assert_review_route_helpers_not_called(calls, helper_calls)


@pytest.mark.parametrize("headers", ADJACENT_ROLE_HEADERS)
@pytest.mark.parametrize(
    "route_name,method,path,params,body",
    _review_flow_route_cases(),
)
async def test_review_flow_routes_reject_adjacent_roles_before_helpers(
    route_name,
    method,
    path,
    params,
    body,
    headers,
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch, existing_draft=_saved_draft())
    helper_calls = _patch_review_flow_helpers_to_fail(monkeypatch)

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await _call_review_flow_route(client, method, path, params, body)

    assert response.status_code == 403, route_name
    rendered = json.dumps(response.json()).lower()
    assert "permission_denied" in rendered
    assert "acme-distribution" not in rendered
    _assert_no_raw_leaks(response.json())
    _assert_review_route_helpers_not_called(calls, helper_calls)


async def test_admin_onboarding_dry_run_requires_auth(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    def fail_validation(*args, **kwargs):  # pragma: no cover
        raise AssertionError("validation should not be called")

    monkeypatch.setattr(admin_onboarding, "validate_onboarding_draft", fail_validation)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/admin/onboarding/validate", json=_complete_draft_payload()
        )

    assert response.status_code == 401
    _assert_no_draft_repo_persistence(calls)


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
async def test_admin_onboarding_dry_run_rejects_adjacent_roles(
    headers,
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch)

    def fail_validation(*args, **kwargs):  # pragma: no cover
        raise AssertionError("validation should not be called")

    monkeypatch.setattr(admin_onboarding, "validate_onboarding_draft", fail_validation)

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.post(
            "/admin/onboarding/validate", json=_complete_draft_payload()
        )

    assert response.status_code == 403
    rendered = json.dumps(response.json()).lower()
    assert "permission_denied" in rendered
    assert "tenant_code" not in rendered
    assert "traceback" not in rendered
    assert "sql" not in rendered
    _assert_no_draft_repo_persistence(calls)


@pytest.mark.parametrize(
    "headers",
    [ADMIN_HEADERS, DISTRIBUTION_ADMIN_HEADERS, SYSTEM_ADMIN_HEADERS],
)
async def test_admin_onboarding_dry_run_returns_validation_without_persistence(
    headers,
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch)

    def fail_audit_evidence(*args, **kwargs):  # pragma: no cover
        raise AssertionError("dry-run must not build audit evidence")

    monkeypatch.setattr(
        admin_onboarding,
        "build_draft_save_audit_evidence",
        fail_audit_evidence,
    )
    monkeypatch.setattr(
        admin_onboarding,
        "build_draft_save_audit_link_fields",
        fail_audit_evidence,
    )

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.post(
            "/admin/onboarding/validate", json=_complete_draft_payload()
        )

    assert response.status_code == 200
    body = response.json()
    rendered = json.dumps(body)
    assert body["status"] == "ok"
    assert body["no_persistence_confirmed"] is True
    assert body["no_live_action_confirmed"] is True
    assert body["readiness_preview"]["overall_status"] == "GO_LIVE_DISABLED"
    assert body["validation_result"]["validated_scope"]["external_tenant_ref"] == (
        "acme-distribution"
    )
    assert "DRY_RUN_ONLY" in body["guardrails"]
    assert "NO_PERSISTENCE" in body["guardrails"]
    assert "NO_AUDIT_WRITE" in body["guardrails"]
    assert "NO_EVENT_DISPATCH" in body["guardrails"]
    assert "NO_WEBHOOK_DELIVERY" in body["guardrails"]
    assert "NO_MONEY_MOVEMENT" in body["guardrails"]
    assert "draft-save-key-1" not in rendered
    assert "tenant_code" not in body["validation_result"]["validated_scope"]
    assert "saved" not in rendered.lower()
    assert "activated" not in rendered.lower()
    _assert_no_draft_repo_persistence(calls)


async def test_admin_onboarding_dry_run_trims_external_scope(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    async with AsyncClient(
        app=app, base_url="http://test", headers=DISTRIBUTION_ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/validate",
            json={
                "scope": {
                    "external_tenant_ref": " acme-distribution ",
                    "organisation_ref": " org-acme ",
                    "producer_ref": " prod-acme ",
                    "sponsor_ref": " sponsor-acme ",
                    "distributor_ref": " dist-acme ",
                    "campaign_code": " CAMP-ACME ",
                    "opportunity_ref": " opp-acme ",
                },
                "validation_scope": ["company", "readiness"],
                "sections": {},
            },
        )

    assert response.status_code == 200
    scope = response.json()["validation_result"]["validated_scope"]
    assert scope["external_tenant_ref"] == "acme-distribution"
    assert scope["organisation_ref"] == "org-acme"
    assert scope["producer_ref"] == "prod-acme"
    assert scope["sponsor_ref"] == "sponsor-acme"
    assert scope["distributor_ref"] == "dist-acme"
    assert scope["campaign_code"] == "CAMP-ACME"
    assert scope["opportunity_ref"] == "opp-acme"
    assert "tenant_code" not in scope
    _assert_no_draft_repo_persistence(calls)


async def test_admin_onboarding_dry_run_missing_evidence_is_explicit(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/validate",
            json={
                "external_tenant_ref": "unknown-demo-tenant",
                "validation_scope": ["company", "readiness"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["validation_result"]["status"] == "MISSING_EVIDENCE"
    assert body["missing_evidence"]
    assert body["readiness_preview"]["overall_status"] == "GO_LIVE_DISABLED"
    assert "traceback" not in json.dumps(body).lower()
    assert "sql" not in json.dumps(body).lower()
    _assert_no_draft_repo_persistence(calls)


async def test_admin_onboarding_dry_run_reports_malformed_sections_safely(
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch)
    payload = _complete_draft_payload()
    payload["sections"]["campaign_opportunity"]["producer_ref"] = "different-producer"

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/validate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["validation_result"]["status"] == "INVALID"
    assert any(item["code"] == "CROSS_SECTION_MISMATCH" for item in body["safe_errors"])
    assert body["no_persistence_confirmed"] is True
    _assert_no_draft_repo_persistence(calls)


async def test_admin_onboarding_dry_run_rejects_tenant_code_without_exposure(
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch)
    payload = _complete_draft_payload(tenant_code="INTERNAL_ACME")

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/validate", json=payload)

    rendered = json.dumps(response.json())
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSAFE_OPERATION_ATTEMPTED"
    assert response.json()["detail"]["no_live_action_confirmed"] is True
    assert "INTERNAL_ACME" not in rendered
    assert "traceback" not in rendered.lower()
    _assert_no_draft_repo_persistence(calls)


async def test_admin_onboarding_dry_run_redacts_secret_and_live_action_payloads(
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch)
    payload = _complete_draft_payload()
    payload["sections"]["webhook_api"]["api_key"] = "SECRET-API-KEY"
    payload["sections"]["webhook_api"]["client_secret"] = "SECRET-CLIENT"
    payload["sections"]["webhook_api"]["access_token"] = "ACCESS-TOKEN"
    payload["sections"]["webhook_api"]["signing_secret"] = "SIGNING-SECRET"
    payload["sections"]["webhook_api"]["private_key"] = "PRIVATE-KEY"
    payload["sections"]["webhook_api"]["provider_payload"] = "PROVIDER-PAYLOAD"
    payload["sections"]["webhook_api"]["audit_payload"] = "AUDIT-PAYLOAD"
    payload["sections"]["webhook_api"]["raw_audit_payload"] = "RAW-AUDIT"
    payload["sections"]["webhook_api"]["deliver_webhook"] = True
    payload["sections"]["webhook_api"]["webhook_delivery_state"] = "DELIVERY-STATE"
    payload["sections"]["campaign_opportunity"]["publish_campaign"] = True
    payload["sections"]["campaign_opportunity"]["create_tenant"] = True
    payload["sections"]["campaign_opportunity"]["create_user"] = True
    payload["sections"]["campaign_opportunity"]["send_invite"] = True
    payload["sections"]["campaign_opportunity"]["activate_go_live"] = True
    payload["sections"]["campaign_opportunity"]["funding_internal"] = "funding-value"
    payload["sections"]["campaign_opportunity"]["wallet_reference"] = "wallet-internal"
    payload["sections"]["campaign_opportunity"]["settlement_batch"] = "settlement-value"
    payload["sections"]["campaign_opportunity"][
        "fulfilment_provider"
    ] = "fulfilment-value"
    payload["sections"]["campaign_opportunity"]["retry_payload"] = "retry-value"
    payload["sections"]["campaign_opportunity"]["money_movement"] = "money-value"

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post("/admin/onboarding/validate", json=payload)

    assert response.status_code == 200
    body = response.json()
    rendered = json.dumps(body)
    assert body["validation_result"]["status"] == "BLOCKED"
    assert body["no_persistence_confirmed"] is True
    assert body["no_live_action_confirmed"] is True
    assert "secret_or_credential" in body["redactions"]
    assert "webhook_internal" in body["redactions"]
    assert "live_action" in body["redactions"]
    assert "money_movement_internal" in body["redactions"]
    assert "provider_internal" in body["redactions"]
    assert "raw_internal" in body["redactions"]
    assert "audit_internal" in body["redactions"]
    assert "retry_internal" in body["redactions"]
    assert "SECRET-API-KEY" not in rendered
    assert "SECRET-CLIENT" not in rendered
    assert "ACCESS-TOKEN" not in rendered
    assert "SIGNING-SECRET" not in rendered
    assert "PRIVATE-KEY" not in rendered
    assert "PROVIDER-PAYLOAD" not in rendered
    assert "AUDIT-PAYLOAD" not in rendered
    assert "RAW-AUDIT" not in rendered
    assert "DELIVERY-STATE" not in rendered
    assert "funding-value" not in rendered
    assert "wallet-internal" not in rendered
    assert "settlement-value" not in rendered
    assert "fulfilment-value" not in rendered
    assert "retry-value" not in rendered
    assert "money-value" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered
    assert "access_token" not in rendered
    assert "private_key" not in rendered
    assert "provider_payload" not in rendered
    assert "audit_payload" not in rendered
    assert "raw_audit_payload" not in rendered
    assert "funding_internal" not in rendered
    assert "event_dispatched" not in rendered
    assert "webhook_dispatched" not in rendered
    assert "create_tenant" not in rendered
    assert "create_user" not in rendered
    assert "send_invite" not in rendered
    assert "publish_campaign" not in rendered
    assert "activate_go_live" not in rendered
    _assert_no_draft_repo_persistence(calls)


async def test_admin_onboarding_draft_save_requires_auth(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/admin/onboarding/drafts", json=_complete_draft_payload()
        )

    assert response.status_code == 401
    assert calls["create_draft"] == []


async def test_admin_onboarding_draft_selector_requires_auth(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/onboarding/drafts")

    assert response.status_code == 401
    assert calls["list_drafts"] == []


async def test_admin_onboarding_draft_selector_rejects_adjacent_role(monkeypatch):
    calls = _patch_draft_repo(monkeypatch)

    async with AsyncClient(
        app=app, base_url="http://test", headers=FINANCE_ADMIN_HEADERS
    ) as client:
        response = await client.get("/admin/onboarding/drafts")

    assert response.status_code == 403
    assert calls["list_drafts"] == []


async def test_admin_onboarding_draft_selector_returns_safe_scope(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        draft_list=[
            _saved_draft(
                draft_ref="draft-safe-1",
                status="READY_FOR_REVIEW",
                safe_summary={
                    "readiness_status": "GO_LIVE_DISABLED",
                    "validation_status": "VALID",
                    "missing_evidence_count": 1,
                    "blocker_count": 0,
                },
                redactions=["internal_identifier"],
                created_by_ref="actor-secret",
            )
        ],
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.get(
            "/admin/onboarding/drafts",
            params={
                "external_tenant_ref": "acme-distribution",
                "organisation_ref": "org-acme",
                "limit": 50,
            },
        )

    assert response.status_code == 200
    body = response.json()
    rendered = json.dumps(body)
    assert body["status"] == "ok"
    assert body["count"] == 1
    assert calls["list_drafts"] == [
        {
            "external_tenant_ref": "acme-distribution",
            "organisation_ref": "org-acme",
            "status": None,
            "limit": 50,
        }
    ]
    item = body["items"][0]
    assert item["draft_ref"] == "draft-safe-1"
    assert item["draft_status"] == "READY_FOR_REVIEW"
    assert item["external_tenant_ref"] == "acme-distribution"
    assert item["organisation_ref"] == "org-acme"
    assert item["readiness_status"] == "GO_LIVE_DISABLED"
    assert item["validation_status"] == "VALID"
    assert item["blocker_count"] == 0
    assert "READ_ONLY_DRAFT_SELECTOR" in body["guardrails"]
    assert "tenant_code" not in rendered
    assert "INTERNAL-ACME" not in rendered
    assert "created_by_ref" not in rendered
    assert "actor-secret" not in rendered


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


async def test_submit_for_review_requires_auth(monkeypatch):
    calls = _patch_draft_repo(monkeypatch, existing_draft=_saved_draft())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(),
        )

    assert response.status_code == 401
    assert calls["update_draft_metadata_or_status"] == []


async def test_submit_for_review_rejects_adjacent_role(monkeypatch):
    calls = _patch_draft_repo(monkeypatch, existing_draft=_saved_draft())

    async with AsyncClient(
        app=app, base_url="http://test", headers=FINANCE_ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(),
        )

    assert response.status_code == 403
    assert calls["update_draft_metadata_or_status"] == []


async def test_submit_for_review_transitions_saved_draft_only(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(),
        )

    body = response.json()
    rendered = json.dumps(body).lower()
    assert response.status_code == 200
    assert body["status"] == "submitted_for_review"
    assert body["draft_ref"] == "draft-submit-1"
    assert body["draft_status"] == "READY_FOR_REVIEW"
    assert body["idempotency_status"] == "NEW_REQUEST"
    assert body["no_live_action_confirmed"] is True
    assert body["audit_evidence_ref"] == "SUBMIT_FOR_REVIEW_AUDIT_EVIDENCE"
    assert body["audit_link_ref"] == "audit-link-uuid"
    assert body["audit_evidence_status"] == "RECORDED_REFERENCE"
    assert calls["update_draft_metadata_or_status"][0]["status"] == "READY_FOR_REVIEW"
    assert calls["update_draft_metadata_or_status"][0]["expected_draft_version"] == 2
    assert calls["record_idempotency_reference"][0]["operation_type"] == (
        "ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW"
    )
    assert len(calls["create_audit_link_reference"]) == 1
    audit_link = calls["create_audit_link_reference"][0]
    assert audit_link["action_type"] == "ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW"
    assert audit_link["action_status"] == "SUCCESS"
    assert audit_link["evidence_type"] == "SUBMIT_FOR_REVIEW_AUDIT_EVIDENCE"
    assert audit_link["audit_ref"] is None
    assert audit_link["event_ref"] is None
    assert audit_link["actor_ref"] == "ADMIN"
    assert audit_link["actor_role"] == "ADMIN"
    assert audit_link["correlation_id"] == "corr-submit-1"
    assert audit_link["changed_sections"] == ["draft_status", "draft_version"]
    assert audit_link["evidence_summary"]["operation_type"] == (
        "ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW"
    )
    assert audit_link["evidence_summary"]["review_status"] == "READY_FOR_REVIEW"
    assert audit_link["evidence_summary"]["dispatch"] == {
        "event_dispatched": False,
        "webhook_dispatched": False,
        "event_ref": None,
    }
    assert audit_link["evidence_summary"]["no_live_action_confirmed"] is True
    rendered_audit = json.dumps(audit_link).lower()
    assert "submit-review-key-1" not in rendered_audit
    assert "tenant_code" not in rendered_audit
    assert "internal-acme" not in rendered_audit
    assert "submit-review-key-1" not in rendered
    assert "tenant_code" not in rendered
    assert "internal-acme" not in rendered
    assert "secret" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered
    assert "provider_payload" not in rendered
    assert "wallet" not in rendered
    assert "settlement" not in rendered
    assert "fulfilment" not in rendered
    assert "retry" not in rendered
    assert "money_movement" not in rendered
    assert "approved" not in rendered
    assert "activated" not in rendered
    _assert_no_raw_leaks(body)
    _assert_no_raw_leaks(audit_link)
    _assert_submit_did_not_invoke_live_actions(calls)


async def test_submit_for_review_enforces_external_scope(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(external_tenant_ref="wrong-tenant"),
        )

    rendered = json.dumps(response.json()).lower()
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DRAFT_NOT_FOUND"
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["get_draft_sections"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    assert "wrong-tenant" not in rendered
    assert "tenant_code" not in rendered
    _assert_no_raw_leaks(response.json())


@pytest.mark.parametrize(
    ("payload_overrides", "leaked_value"),
    [
        ({"organisation_ref": "wrong-org"}, "wrong-org"),
        ({"producer_ref": "wrong-producer"}, "wrong-producer"),
        ({"distributor_ref": "wrong-distributor"}, "wrong-distributor"),
        ({"campaign_code": "WRONG-CAMPAIGN"}, "wrong-campaign"),
    ],
)
async def test_submit_for_review_rejects_cross_scope_references_safely(
    payload_overrides,
    leaked_value,
    monkeypatch,
):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(**payload_overrides),
        )

    rendered = json.dumps(response.json()).lower()
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DRAFT_NOT_FOUND"
    assert calls["get_draft_by_ref"] == "draft-submit-1"
    assert calls["get_draft_sections"] == []
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    assert leaked_value not in rendered
    _assert_no_raw_leaks(response.json())


async def test_submit_for_review_missing_draft_is_safe_and_non_mutating(
    monkeypatch,
):
    calls = _patch_draft_repo(monkeypatch, existing_draft=None)

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/missing-draft/submit-for-review",
            json=_submit_payload(),
        )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DRAFT_NOT_FOUND"
    assert calls["get_draft_by_ref"] == "missing-draft"
    assert calls["get_draft_sections"] == []
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    _assert_no_raw_leaks(response.json())


async def test_submit_for_review_rejects_user_facing_tenant_code(monkeypatch):
    calls = _patch_draft_repo(monkeypatch, existing_draft=_saved_draft())

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(tenant_code="INTERNAL_ACME"),
        )

    rendered = json.dumps(response.json())
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSAFE_OPERATION_ATTEMPTED"
    assert "INTERNAL_ACME" not in rendered
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["get_draft_sections"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    _assert_no_raw_leaks(response.json())


async def test_submit_for_review_stale_version_returns_safe_error(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(),
        draft_sections=_saved_draft_sections(),
        stale_update=True,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(expected_version=1),
        )

    body = response.json()
    rendered = json.dumps(body).lower()
    assert response.status_code == 409
    assert body["detail"]["code"] == "STALE_DRAFT"
    assert calls["record_idempotency_reference"] == []
    assert "traceback" not in rendered
    assert "sql" not in rendered


async def test_submit_for_review_invalid_state_returns_safe_error(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="DISCARDED"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(),
        )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "INVALID_STATE"
    assert calls["update_draft_metadata_or_status"] == []


async def test_submit_for_review_validation_blockers_prevent_transition(monkeypatch):
    payload = _complete_draft_payload()
    payload["sections"]["campaign_opportunity"]["publish_campaign"] = True
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="VALIDATION_FAILED"),
        draft_sections=_saved_draft_sections(payload),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(),
        )

    body = response.json()
    rendered = json.dumps(body)
    assert response.status_code == 422
    assert body["detail"]["code"] == "VALIDATION_BLOCKED"
    assert body["detail"]["validation_summary"]["status"] == "BLOCKED"
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    assert "publish_campaign" not in rendered
    _assert_no_raw_leaks(body)


async def test_submit_for_review_redacts_unsafe_saved_evidence_and_no_dispatch(
    monkeypatch,
):
    payload = _complete_draft_payload()
    payload["sections"]["webhook_api"]["api_key"] = "SECRET-API-KEY"
    payload["sections"]["webhook_api"]["client_secret"] = "SECRET-CLIENT"
    payload["sections"]["webhook_api"]["access_token"] = "ACCESS-TOKEN"
    payload["sections"]["webhook_api"]["signing_secret"] = "SIGNING-SECRET"
    payload["sections"]["webhook_api"]["private_key"] = "PRIVATE-KEY"
    payload["sections"]["webhook_api"]["provider_payload"] = "PROVIDER-PAYLOAD"
    payload["sections"]["webhook_api"]["audit_payload"] = "AUDIT-PAYLOAD"
    payload["sections"]["webhook_api"]["raw_audit_payload"] = "RAW-AUDIT"
    payload["sections"]["webhook_api"]["webhook_delivery_state"] = "DELIVERY-STATE"
    payload["sections"]["campaign_opportunity"]["publish_campaign"] = True
    payload["sections"]["campaign_opportunity"]["activate_go_live"] = True
    payload["sections"]["campaign_opportunity"]["funding_internal"] = "funding-value"
    payload["sections"]["campaign_opportunity"]["wallet_internal"] = "wallet-internal"
    payload["sections"]["campaign_opportunity"][
        "settlement_internal"
    ] = "settlement-value"
    payload["sections"]["campaign_opportunity"][
        "fulfilment_internal"
    ] = "fulfilment-value"
    payload["sections"]["campaign_opportunity"]["retry_internal"] = "retry-value"
    payload["sections"]["campaign_opportunity"]["money_movement_detail"] = "money-value"
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="VALIDATION_FAILED"),
        draft_sections=_saved_draft_sections(payload),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=_submit_payload(),
        )

    body = response.json()
    assert response.status_code == 422
    assert body["detail"]["code"] == "VALIDATION_BLOCKED"
    assert body["detail"]["audit_evidence_ref"] is None
    assert body["detail"]["audit_link_ref"] is None
    assert body["detail"]["no_live_action_confirmed"] is True
    assert "NO_WEBHOOK_DISPATCH" in body["detail"]["guardrails"]
    assert "NO_VALUE_TRANSFER" in body["detail"]["guardrails"]
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    _assert_no_raw_leaks(body)


async def test_submit_for_review_replays_same_idempotency_payload(monkeypatch):
    payload = _submit_payload()
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
        existing_idempotency=_existing_submit_idempotency_for(payload),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=payload,
        )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "replayed"
    assert body["idempotency_status"] == "REPLAY_SAME_PAYLOAD"
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []


async def test_submit_for_review_conflicts_on_different_idempotency_payload(
    monkeypatch,
):
    payload = _submit_payload()
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(),
        draft_sections=_saved_draft_sections(),
        existing_idempotency=_existing_submit_idempotency_for(
            payload,
            request_hash="different-request-hash",
        ),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/submit-for-review",
            json=payload,
        )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert calls["update_draft_metadata_or_status"] == []


async def test_review_decision_records_internal_approval_without_live_actions(
    monkeypatch,
):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(),
        )

    body = response.json()
    rendered = json.dumps(body).lower()
    assert response.status_code == 200
    assert body["status"] == "review_decision_recorded"
    assert body["draft_ref"] == "draft-submit-1"
    assert body["previous_status"] == "READY_FOR_REVIEW"
    assert body["draft_status"] == "READY_FOR_REVIEW"
    assert body["review_outcome"] == (
        review_service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW
    )
    assert body["approval_to_launch"] is False
    assert body["go_live_enabled"] is False
    assert body["audit_evidence_ref"] == "REVIEW_DECISION_AUDIT_EVIDENCE"
    assert body["audit_link_ref"] == "audit-link-uuid"
    assert body["audit_evidence_status"] == "RECORDED_REFERENCE"
    assert body["no_live_action_confirmed"] is True
    assert "NO_APPROVAL_TO_LAUNCH" in body["guardrails"]
    assert "NO_WEBHOOK_DISPATCH" in body["guardrails"]
    assert "NO_VALUE_TRANSFER" in body["guardrails"]
    assert calls["update_draft_metadata_or_status"][0]["status"] == (
        "READY_FOR_REVIEW"
    )
    assert calls["update_draft_metadata_or_status"][0]["expected_draft_version"] == 2
    assert calls["record_idempotency_reference"][0]["operation_type"] == (
        review_service.OPERATION_REVIEW_DECISION
    )
    assert len(calls["create_audit_link_reference"]) == 1
    audit_link = calls["create_audit_link_reference"][0]
    assert audit_link["action_type"] == review_service.OPERATION_REVIEW_DECISION
    assert audit_link["action_status"] == "SUCCESS"
    assert audit_link["evidence_type"] == "REVIEW_DECISION_AUDIT_EVIDENCE"
    assert audit_link["audit_ref"] is None
    assert audit_link["event_ref"] is None
    assert audit_link["actor_ref"] == "ADMIN"
    assert audit_link["actor_role"] == "ADMIN"
    assert audit_link["correlation_id"] == "corr-review-1"
    assert audit_link["evidence_summary"]["review_outcome"] == (
        review_service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW
    )
    assert audit_link["evidence_summary"]["reason_reference"]
    assert audit_link["evidence_summary"]["dispatch"] == {
        "event_dispatched": False,
        "webhook_dispatched": False,
        "event_ref": None,
    }
    rendered_audit = json.dumps(audit_link).lower()
    assert "review-decision-key-1" not in rendered_audit
    assert "evidence is complete" not in rendered_audit
    assert "tenant_code" not in rendered_audit
    assert "internal-acme" not in rendered_audit
    assert "review-decision-key-1" not in rendered
    assert "evidence is complete" not in rendered
    assert "tenant_code" not in rendered
    assert "internal-acme" not in rendered
    assert "approved_to_launch" not in rendered
    assert "activated" not in rendered
    _assert_no_raw_leaks(body)
    _assert_submit_did_not_invoke_live_actions(calls)


async def test_review_decision_records_schema_backed_blocked_status(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=SYSTEM_ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(
                review_outcome=review_service.OUTCOME_BLOCKED,
                reason_category="MISSING_POLICY_SIGNOFF",
                reason="Policy sign-off is required before this can continue.",
            ),
        )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "review_decision_recorded"
    assert body["draft_status"] == "BLOCKED"
    assert body["review_outcome"] == review_service.OUTCOME_BLOCKED
    assert calls["update_draft_metadata_or_status"][0]["status"] == "BLOCKED"
    assert len(calls["create_audit_link_reference"]) == 1
    assert calls["create_audit_link_reference"][0]["evidence_summary"][
        "review_status"
    ] == "BLOCKED"
    rendered_update = json.dumps(calls["update_draft_metadata_or_status"][0]).lower()
    assert "policy sign-off" not in rendered_update


@pytest.mark.parametrize(
    "headers,expected_actor_role",
    [
        (ADMIN_HEADERS, "ADMIN"),
        (DISTRIBUTION_ADMIN_HEADERS, "DISTRIBUTION_ADMIN"),
        (SYSTEM_ADMIN_HEADERS, "SYSTEM_ADMIN"),
    ],
)
async def test_review_decision_allows_only_admin_operator_roles_with_safe_audit(
    headers,
    expected_actor_role,
    monkeypatch,
):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(app=app, base_url="http://test", headers=headers) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(
                idempotency_key=f"review-decision-{expected_actor_role.lower()}",
            ),
        )

    body = response.json()
    rendered = json.dumps(body).lower()
    assert response.status_code == 200
    assert body["status"] == "review_decision_recorded"
    assert body["approval_to_launch"] is False
    assert body["go_live_enabled"] is False
    assert body["audit_evidence_ref"] == "REVIEW_DECISION_AUDIT_EVIDENCE"
    assert len(calls["create_audit_link_reference"]) == 1
    audit_link = calls["create_audit_link_reference"][0]
    assert audit_link["actor_role"] == expected_actor_role
    assert audit_link["evidence_summary"]["dispatch"] == {
        "event_dispatched": False,
        "webhook_dispatched": False,
        "event_ref": None,
    }
    assert "tenant_code" not in rendered
    assert "internal-acme" not in rendered
    assert "approval_to_launch\": true" not in rendered
    _assert_no_raw_leaks(body)
    _assert_no_raw_leaks(audit_link)
    _assert_submit_did_not_invoke_live_actions(calls)


async def test_review_decision_rejects_nested_tenant_code_before_lookup(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(
                scope={
                    "tenant_code": "INTERNAL-ACME",
                    "external_tenant_ref": "acme-distribution",
                }
            ),
        )

    rendered = json.dumps(response.json()).lower()
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSAFE_OPERATION_ATTEMPTED"
    assert calls["get_draft_sections"] == []
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    assert "internal-acme" not in rendered
    _assert_no_raw_leaks(response.json())


async def test_review_decision_redacts_hostile_saved_evidence_and_no_dispatch(
    monkeypatch,
):
    payload = _complete_draft_payload()
    payload["sections"]["webhook_api"]["api_key"] = "SECRET-API-KEY"
    payload["sections"]["webhook_api"]["client_secret"] = "SECRET-CLIENT"
    payload["sections"]["webhook_api"]["access_token"] = "ACCESS-TOKEN"
    payload["sections"]["webhook_api"]["signing_secret"] = "SIGNING-SECRET"
    payload["sections"]["webhook_api"]["private_key"] = "PRIVATE-KEY"
    payload["sections"]["webhook_api"]["provider_payload"] = "PROVIDER-PAYLOAD"
    payload["sections"]["webhook_api"]["audit_payload"] = "AUDIT-PAYLOAD"
    payload["sections"]["webhook_api"]["raw_audit_payload"] = "RAW-AUDIT"
    payload["sections"]["webhook_api"]["webhook_delivery_state"] = "DELIVERY-STATE"
    payload["sections"]["campaign_opportunity"]["funding_internal"] = "funding-value"
    payload["sections"]["campaign_opportunity"]["wallet_internal"] = "wallet-internal"
    payload["sections"]["campaign_opportunity"][
        "settlement_internal"
    ] = "settlement-value"
    payload["sections"]["campaign_opportunity"][
        "fulfilment_internal"
    ] = "fulfilment-value"
    payload["sections"]["campaign_opportunity"]["retry_internal"] = "retry-value"
    payload["sections"]["campaign_opportunity"]["money_movement_detail"] = (
        "money-value"
    )
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(
            status="READY_FOR_REVIEW",
            provider_payload="PROVIDER-PAYLOAD",
            audit_payload="AUDIT-PAYLOAD",
            webhook_delivery_state="DELIVERY-STATE",
            wallet_ref="wallet-internal",
            settlement_ref="settlement-internal",
        ),
        draft_sections=_saved_draft_sections(payload),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(
                reason=(
                    "Evidence looks complete, but this reason must remain "
                    "hash-only in audit evidence."
                )
            ),
        )

    body = response.json()
    assert response.status_code == 422
    assert body["detail"]["code"] == "VALIDATION_BLOCKED"
    assert body["detail"]["audit_evidence_ref"] is None
    assert body["detail"]["audit_link_ref"] is None
    assert body["detail"]["approval_to_launch"] is False
    assert body["detail"]["go_live_enabled"] is False
    assert body["detail"]["no_live_action_confirmed"] is True
    assert "NO_WEBHOOK_DISPATCH" in body["detail"]["guardrails"]
    assert "NO_VALUE_TRANSFER" in body["detail"]["guardrails"]
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    rendered = json.dumps(body).lower()
    assert "evidence looks complete" not in rendered
    _assert_no_raw_leaks(body)
    _assert_submit_did_not_invoke_live_actions(calls)


async def test_review_decision_enforces_external_scope(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(external_tenant_ref="wrong-tenant"),
        )

    rendered = json.dumps(response.json()).lower()
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DRAFT_NOT_FOUND"
    assert calls["get_draft_sections"] == []
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert "wrong-tenant" not in rendered
    assert "tenant_code" not in rendered
    _assert_no_raw_leaks(response.json())


async def test_review_decision_stale_version_returns_safe_error(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
        stale_update=True,
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(expected_version=1),
        )

    body = response.json()
    rendered = json.dumps(body).lower()
    assert response.status_code == 409
    assert body["detail"]["code"] == "STALE_DRAFT"
    assert calls["record_idempotency_reference"] == []
    assert "traceback" not in rendered
    assert "sql" not in rendered
    _assert_no_raw_leaks(body)


async def test_review_decision_invalid_state_returns_safe_error(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="DRAFT_UPDATED"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(),
        )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "INVALID_STATE"
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []


async def test_review_decision_validation_blockers_prevent_decision(monkeypatch):
    payload = _complete_draft_payload()
    payload["sections"]["campaign_opportunity"]["publish_campaign"] = True
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(payload),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(),
        )

    body = response.json()
    rendered = json.dumps(body)
    assert response.status_code == 422
    assert body["detail"]["code"] == "VALIDATION_BLOCKED"
    assert body["detail"]["validation_summary"]["status"] == "BLOCKED"
    assert body["detail"]["audit_evidence_ref"] is None
    assert body["detail"]["audit_link_ref"] is None
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []
    assert "publish_campaign" not in rendered
    _assert_no_raw_leaks(body)


async def test_review_decision_rejects_unsupported_schema_outcome(monkeypatch):
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=_review_payload(review_outcome=review_service.OUTCOME_REJECTED),
        )

    body = response.json()
    assert response.status_code == 422
    assert body["detail"]["code"] == "UNSUPPORTED_SCHEMA_STATE"
    assert body["detail"]["review_outcome"] == review_service.OUTCOME_REJECTED
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []


async def test_review_decision_replays_same_idempotency_payload(monkeypatch):
    payload = _review_payload()
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
        existing_idempotency=_existing_review_idempotency_for(payload),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=payload,
        )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "replayed"
    assert body["idempotency_status"] == "REPLAY_SAME_PAYLOAD"
    assert calls["update_draft_metadata_or_status"] == []
    assert calls["record_idempotency_reference"] == []
    assert calls["create_audit_link_reference"] == []


async def test_review_decision_conflicts_on_different_idempotency_payload(
    monkeypatch,
):
    payload = _review_payload()
    calls = _patch_draft_repo(
        monkeypatch,
        existing_draft=_saved_draft(status="READY_FOR_REVIEW"),
        draft_sections=_saved_draft_sections(),
        existing_idempotency=_existing_review_idempotency_for(
            payload,
            request_hash="different-request-hash",
        ),
    )

    async with AsyncClient(
        app=app, base_url="http://test", headers=ADMIN_HEADERS
    ) as client:
        response = await client.post(
            "/admin/onboarding/drafts/draft-submit-1/review-decision",
            json=payload,
        )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert calls["update_draft_metadata_or_status"] == []
