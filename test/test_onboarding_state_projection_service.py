from __future__ import annotations

import copy
import json

from services.onboarding.onboarding_state_projection_service import (
    EVIDENCE_PARTIAL,
    EVIDENCE_PRESENT,
    EVIDENCE_SHELL_ONLY,
    EVIDENCE_UNKNOWN_REFERENCE,
    STATUS_BLOCKED,
    STATUS_IN_PROGRESS,
    STATUS_READY,
    STATUS_REVIEW_ONLY,
    STATUS_UNAVAILABLE,
    project_onboarding_state,
)

GENERATED_AT = "2026-06-28T00:00:00Z"


def _complete_evidence():
    return {
        "scope": {
            "external_tenant_ref": "acme-distribution",
            "organisation_ref": "org-acme",
            "producer_ref": "prod-acme",
            "sponsor_ref": "sponsor-acme",
            "distributor_ref": "dist-acme",
            "campaign_code": "CAMP-ACME",
            "opportunity_ref": "opp-acme",
            "tenant_code": "INTERNAL_ACME",
        },
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


def test_complete_projection_uses_external_refs_and_ready_sections():
    result = project_onboarding_state(_complete_evidence(), generated_at=GENERATED_AT)

    assert result["contract_version"] == "onboarding.v1"
    assert result["generated_at"] == GENERATED_AT
    assert result["scope"]["external_tenant_ref"] == "acme-distribution"
    assert result["scope"]["organisation_ref"] == "org-acme"
    assert "tenant_code" not in result["scope"]["resolved_tenant"]
    assert result["redactions"] == ["internal_identifier"]

    for section in result["sections"].values():
        assert section["status"] == STATUS_READY
        assert section["evidence_status"] == EVIDENCE_PRESENT
        assert section["missing_evidence"] == []

    assert result["readiness"]["status"] == STATUS_REVIEW_ONLY
    assert result["readiness"]["summary"] == {
        "ready_count": 6,
        "blocked_count": 2,
        "total_count": 8,
    }
    assert "NO_MONEY_MOVEMENT" in result["guardrails"]


def test_partial_projection_marks_missing_fields():
    result = project_onboarding_state(
        {
            "sections": {
                "company": {
                    "organisation_name": "Acme Distribution",
                    "external_tenant_ref": "acme-distribution",
                }
            }
        },
        generated_at=GENERATED_AT,
    )

    company = result["sections"]["company"]
    assert company["status"] == STATUS_IN_PROGRESS
    assert company["evidence_status"] == EVIDENCE_PARTIAL
    assert company["missing_evidence"][0]["code"] == "MISSING_REQUIRED_FIELD"
    assert "organisation_ref" in company["blockers"][0]
    assert result["sections"]["producer_sponsor"]["status"] == STATUS_UNAVAILABLE
    assert (
        result["sections"]["producer_sponsor"]["evidence_status"] == EVIDENCE_SHELL_ONLY
    )


def test_missing_evidence_projection_marks_shell_only_sections():
    result = project_onboarding_state(generated_at=GENERATED_AT)

    assert result["scope"]["resolved_tenant"]["status"] == STATUS_UNAVAILABLE
    assert all(
        section["evidence_status"] == EVIDENCE_SHELL_ONLY
        for section in result["sections"].values()
    )
    assert all(
        section["status"] == STATUS_UNAVAILABLE
        for section in result["sections"].values()
    )
    assert any(
        item["code"] == "NO_BACKEND_SOURCE" for item in result["missing_evidence"]
    )
    assert any(
        item["code"] == "NO_RESOLVED_TENANT" for item in result["missing_evidence"]
    )


def test_unknown_reference_projection_blocks_affected_section():
    result = project_onboarding_state(
        {
            "scope": {
                "external_tenant_ref": "missing-tenant",
                "unknown_references": ["external_tenant_ref"],
            },
            "sections": {
                "distributor": {
                    "distributor_ref": "missing-distributor",
                    "unknown_reference": True,
                }
            },
        },
        generated_at=GENERATED_AT,
    )

    distributor = result["sections"]["distributor"]
    assert result["scope"]["resolved_tenant"]["status"] == EVIDENCE_UNKNOWN_REFERENCE
    assert distributor["status"] == STATUS_BLOCKED
    assert distributor["evidence_status"] == EVIDENCE_UNKNOWN_REFERENCE
    assert distributor["missing_evidence"][0]["code"] == "UNKNOWN_REFERENCE"
    assert result["readiness"]["summary"]["blocked_count"] == 3


def test_projection_redacts_unsafe_values_and_does_not_mutate_input():
    evidence = _complete_evidence()
    evidence["scope"]["tenant_code"] = "INTERNAL_ACME"
    evidence["sections"]["webhook_api"].update(
        {
            "api_key": "secret-key-value",
            "client_secret": "secret-client-value",
            "provider_payload": {"raw": "provider-value"},
            "wallet_account": "wallet-internal",
            "raw_audit_payload": "audit-internal",
        }
    )
    original = copy.deepcopy(evidence)

    result = project_onboarding_state(evidence, generated_at=GENERATED_AT)
    rendered = json.dumps(result)

    assert evidence == original
    assert "tenant_code" not in result["scope"]["resolved_tenant"]
    assert "secret-key-value" not in rendered
    assert "secret-client-value" not in rendered
    assert "provider-value" not in rendered
    assert "wallet-internal" not in rendered
    assert "audit-internal" not in rendered
    assert sorted(result["redactions"]) == [
        "audit_internal",
        "internal_identifier",
        "money_movement_internal",
        "provider_internal",
        "raw_internal",
        "secret_or_credential",
    ]
