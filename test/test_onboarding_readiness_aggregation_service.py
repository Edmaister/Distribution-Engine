from __future__ import annotations

import copy
import json

from services.onboarding.onboarding_readiness_aggregation_service import (
    READINESS_BLOCKED,
    READINESS_GO_LIVE_DISABLED,
    READINESS_IN_PROGRESS,
    READINESS_MISSING_EVIDENCE,
    READINESS_PERMISSION_LIMITED,
    READINESS_READY,
    aggregate_onboarding_readiness,
)
from services.onboarding.onboarding_state_projection_service import (
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


def _aggregate(evidence):
    projection = project_onboarding_state(evidence, generated_at=GENERATED_AT)
    return aggregate_onboarding_readiness(projection, generated_at=GENERATED_AT)


def _category(result, category):
    return next(item for item in result["categories"] if item["category"] == category)


def test_ready_state_aggregates_present_projection_sections():
    result = _aggregate(_complete_evidence())

    assert result["scope"]["external_tenant_ref"] == "acme-distribution"
    assert "tenant_code" not in result["scope"]["resolved_tenant"]
    assert _category(result, "ORGANISATION_PROFILE")["status"] == READINESS_READY
    assert _category(result, "WEBHOOK_API_SETUP")["status"] == READINESS_READY
    assert result["summary"]["ready_count"] == 6
    assert result["summary"]["total_count"] == 8
    assert result["overall_status"] == READINESS_GO_LIVE_DISABLED
    assert "GO_LIVE_DISABLED" in result["guardrails"]


def test_in_progress_state_uses_partial_projection_evidence():
    result = _aggregate(
        {
            "sections": {
                "company": {
                    "organisation_name": "Acme Distribution",
                    "external_tenant_ref": "acme-distribution",
                }
            }
        }
    )

    company = _category(result, "ORGANISATION_PROFILE")
    assert company["status"] == READINESS_IN_PROGRESS
    assert company["source_evidence_refs"][0]["evidence_status"] == "PARTIAL"
    assert company["blockers"]
    assert result["summary"]["in_progress_count"] == 1


def test_blocked_state_uses_unknown_reference_projection():
    result = _aggregate(
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
        }
    )

    distributor = _category(result, "DISTRIBUTOR_SETUP")
    assert distributor["status"] == READINESS_BLOCKED
    assert distributor["source_evidence_refs"][0]["missing_evidence_codes"] == [
        "UNKNOWN_REFERENCE"
    ]
    assert result["summary"]["blocked_count"] >= 2


def test_missing_evidence_state_keeps_shell_only_categories_not_live_ready():
    result = aggregate_onboarding_readiness(
        project_onboarding_state(generated_at=GENERATED_AT),
        generated_at=GENERATED_AT,
    )

    company = _category(result, "ORGANISATION_PROFILE")
    assert company["status"] == READINESS_MISSING_EVIDENCE
    assert company["safe_display_status"]["action_required"] is True
    assert company["source_evidence_refs"][0]["missing_evidence_codes"] == [
        "NO_BACKEND_SOURCE"
    ]
    assert result["summary"]["missing_evidence_count"] == 6


def test_permission_limited_state_overrides_category_without_leaking_evidence():
    result = aggregate_onboarding_readiness(
        project_onboarding_state(_complete_evidence(), generated_at=GENERATED_AT),
        permission_limited_categories=["MEMBERS_AND_ROLES"],
        generated_at=GENERATED_AT,
    )

    members = _category(result, "MEMBERS_AND_ROLES")
    assert members["status"] == READINESS_PERMISSION_LIMITED
    assert members["safe_display_status"]["label"] == "Permission limited"
    assert members["blockers"] == [
        "Current identity cannot see all evidence for this category."
    ]
    assert result["summary"]["permission_limited_count"] == 1


def test_go_live_controls_remain_disabled():
    result = _aggregate(_complete_evidence())

    go_live = _category(result, "GO_LIVE_CONTROLS")
    assert go_live["status"] == READINESS_GO_LIVE_DISABLED
    assert go_live["safe_display_status"]["go_live_enabled"] is False
    assert any("disabled" in blocker.lower() for blocker in go_live["blockers"])
    assert go_live["source_evidence_refs"][0]["missing_evidence_codes"] == [
        "LIVE_DB_VERIFICATION_BLOCKED",
        "DRIFT_VERIFICATION_BLOCKED",
    ]


def test_redaction_safe_output_and_no_mutation():
    projection = project_onboarding_state(
        _complete_evidence(), generated_at=GENERATED_AT
    )
    projection["scope"]["resolved_tenant"]["tenant_code"] = "INTERNAL_ACME"
    projection["internal_id"] = "internal-row-1"
    projection["raw_audit_payload"] = "audit-internal"
    projection["sections"]["webhook_api"]["data"]["client_secret"] = "secret-value"
    projection["sections"]["producer_sponsor"]["data"]["wallet_account"] = "wallet-1"
    original = copy.deepcopy(projection)

    result = aggregate_onboarding_readiness(projection, generated_at=GENERATED_AT)
    rendered = json.dumps(result)

    assert projection == original
    assert "tenant_code" not in result["scope"]["resolved_tenant"]
    assert "INTERNAL_ACME" not in rendered
    assert "internal-row-1" not in rendered
    assert "audit-internal" not in rendered
    assert "secret-value" not in rendered
    assert "wallet-1" not in rendered
    assert sorted(result["redactions"]) == [
        "audit_internal",
        "internal_identifier",
        "money_movement_internal",
        "raw_internal",
        "secret_or_credential",
    ]
