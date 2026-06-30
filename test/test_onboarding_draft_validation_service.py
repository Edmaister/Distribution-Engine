import copy
import json

from services.onboarding.onboarding_draft_validation_service import (
    ERROR_CROSS_SECTION_MISMATCH,
    ERROR_GO_LIVE_DISABLED,
    ERROR_PERMISSION_DENIED,
    ERROR_REQUIRED_FIELD_MISSING,
    ERROR_UNSAFE_FIELD,
    ERROR_UNSAFE_OPERATION,
    VALIDATION_INVALID,
    VALIDATION_PERMISSION_LIMITED,
    VALIDATION_VALID,
    validate_onboarding_draft,
)

GENERATED_AT = "2026-06-30T00:00:00Z"


def _complete_draft():
    return {
        "scope": {
            "external_tenant_ref": "acme-distribution",
            "organisation_ref": "org-acme",
            "producer_ref": "prod-acme",
            "sponsor_ref": "sponsor-acme",
            "distributor_ref": "dist-acme",
            "campaign_code": "CAMP-ACME",
            "opportunity_ref": "opp-acme",
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


def _codes(items):
    return {item["code"] for item in items}


def test_valid_minimal_draft_produces_readiness_preview_without_mutation():
    draft = _complete_draft()
    original = copy.deepcopy(draft)

    result = validate_onboarding_draft(draft, generated_at=GENERATED_AT)
    rendered = json.dumps(result)

    assert draft == original
    assert result["status"] == "ok"
    assert result["validation_result"]["status"] == VALIDATION_VALID
    assert result["validation_result"]["validated_sections"] == [
        "campaign_opportunity",
        "company",
        "distributor",
        "member_role",
        "producer_sponsor",
        "webhook_api",
    ]
    assert result["readiness_preview"]["summary"]["ready_count"] == 6
    assert result["readiness_preview"]["overall_status"] == "GO_LIVE_DISABLED"
    assert result["no_persistence_confirmed"] is True
    assert "NO_PERSISTENCE" in result["guardrails"]
    assert "INTERNAL_ACME" not in rendered
    assert "tenant_code" not in result["validation_result"]["validated_scope"]


def test_missing_required_fields_produce_safe_errors_and_missing_evidence():
    draft = _complete_draft()
    draft["sections"]["campaign_opportunity"].pop("campaign_code")

    result = validate_onboarding_draft(draft, generated_at=GENERATED_AT)

    assert result["validation_result"]["status"] == VALIDATION_INVALID
    assert ERROR_REQUIRED_FIELD_MISSING in _codes(result["safe_errors"])
    assert any(
        item["section"] == "campaign_opportunity" and item["field"] == "campaign_code"
        for item in result["missing_evidence"]
    )
    assert "Resolve validation blockers before review." in result["next_actions"]


def test_cross_section_mismatch_produces_safe_error():
    draft = _complete_draft()
    draft["sections"]["campaign_opportunity"]["producer_ref"] = "other-producer"

    result = validate_onboarding_draft(draft, generated_at=GENERATED_AT)

    assert result["validation_result"]["status"] == VALIDATION_INVALID
    assert ERROR_CROSS_SECTION_MISMATCH in _codes(result["safe_errors"])
    assert any(
        item["section"] == "campaign_opportunity" and item["field"] == "producer_ref"
        for item in result["blockers"]
    )


def test_permission_context_limits_requested_categories():
    result = validate_onboarding_draft(
        _complete_draft(),
        actor_context={"permission_limited_categories": ["MEMBERS_AND_ROLES"]},
        generated_at=GENERATED_AT,
    )

    assert result["validation_result"]["status"] == VALIDATION_PERMISSION_LIMITED
    assert ERROR_PERMISSION_DENIED in _codes(result["safe_errors"])
    members = next(
        item
        for item in result["readiness_preview"]["categories"]
        if item["category"] == "MEMBERS_AND_ROLES"
    )
    assert members["status"] == "PERMISSION_LIMITED"


def test_missing_sections_remain_explicit_missing_evidence():
    result = validate_onboarding_draft(
        {"scope": {"external_tenant_ref": "acme-distribution"}},
        generated_at=GENERATED_AT,
    )

    assert result["validation_result"]["status"] == "MISSING_EVIDENCE"
    assert result["missing_evidence"]
    assert result["readiness_preview"]["summary"]["missing_evidence_count"] == 6


def test_sensitive_fields_are_omitted_and_not_leaked():
    draft = _complete_draft()
    draft["scope"]["tenant_code"] = "INTERNAL_ACME"
    draft["sections"]["webhook_api"]["api_key"] = "SECRET-API-KEY"
    draft["sections"]["webhook_api"]["client_secret"] = "SECRET-CLIENT"

    result = validate_onboarding_draft(draft, generated_at=GENERATED_AT)
    rendered = json.dumps(result)

    assert ERROR_UNSAFE_FIELD in _codes(result["safe_errors"])
    assert "secret_or_credential" in result["redactions"]
    assert "internal_identifier" in result["redactions"]
    assert "SECRET-API-KEY" not in rendered
    assert "SECRET-CLIENT" not in rendered
    assert "INTERNAL_ACME" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered


def test_live_action_attempts_are_blocked_without_side_effects():
    draft = _complete_draft()
    draft["sections"]["campaign_opportunity"]["publish_campaign"] = True
    draft["sections"]["webhook_api"]["deliver_webhook"] = True

    result = validate_onboarding_draft(draft, generated_at=GENERATED_AT)

    assert ERROR_UNSAFE_OPERATION in _codes(result["safe_errors"])
    assert "live_action" in result["redactions"]
    assert "webhook_internal" in result["redactions"]
    assert result["no_persistence_confirmed"] is True


def test_go_live_controls_remain_disabled_for_valid_draft():
    result = validate_onboarding_draft(_complete_draft(), generated_at=GENERATED_AT)

    assert ERROR_GO_LIVE_DISABLED in _codes(result["warnings"])
    go_live = next(
        item
        for item in result["readiness_preview"]["categories"]
        if item["category"] == "GO_LIVE_CONTROLS"
    )
    assert go_live["safe_display_status"]["go_live_enabled"] is False
    assert "Keep go-live and live platform actions disabled." in result["next_actions"]


def test_money_and_retry_internals_are_not_returned():
    draft = _complete_draft()
    draft["sections"]["producer_sponsor"]["wallet_account"] = "WALLET-1"
    draft["sections"]["campaign_opportunity"]["funding_reservation"] = "FUND-1"
    draft["sections"]["campaign_opportunity"]["retry_job"] = "RETRY-1"

    result = validate_onboarding_draft(draft, generated_at=GENERATED_AT)
    rendered = json.dumps(result)

    assert ERROR_UNSAFE_OPERATION in _codes(result["safe_errors"])
    assert "money_movement_internal" in result["redactions"]
    assert "retry_internal" in result["redactions"]
    assert "WALLET-1" not in rendered
    assert "FUND-1" not in rendered
    assert "RETRY-1" not in rendered
