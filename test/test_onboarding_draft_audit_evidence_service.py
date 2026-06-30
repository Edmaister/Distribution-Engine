import json

from services.onboarding.onboarding_draft_audit_evidence_service import (
    EMPTY_STATE_HASH,
    build_draft_save_audit_evidence,
    build_draft_save_audit_link_fields,
)


def _validation(**overrides):
    payload = {
        "validation_result": {"status": "MISSING_EVIDENCE"},
        "readiness_preview": {
            "overall_status": "GO_LIVE_DISABLED",
            "summary": {
                "ready_count": 2,
                "blocked_count": 0,
                "missing_evidence_count": 1,
                "go_live_disabled_count": 8,
                "total_count": 8,
            },
        },
        "safe_errors": [],
        "missing_evidence": [{"code": "NO_CREDENTIAL_SOURCE"}],
        "blockers": [],
        "redactions": ["TENANT_CODE_INTERNAL", "SECRETS_REDACTED"],
    }
    payload.update(overrides)
    return payload


def _evidence(**overrides):
    params = {
        "actor_ref": "operator-1",
        "actor_role": "platform_admin",
        "permission_scope": {
            "route_family": "admin_onboarding",
            "role_family": "platform_operator",
        },
        "external_scope": {
            "external_tenant_ref": "acme-distribution",
            "organisation_ref": "org-acme",
            "producer_ref": "prod-acme",
            "campaign_code": "CAMP-ACME",
        },
        "draft_ref": "draft_001",
        "draft_version": 1,
        "action_status": "success",
        "idempotency_reference": "idempotency-hash-reference",
        "correlation_id": "corr-123",
        "current_sections": {
            "company": {
                "organisation_name": "Acme Distribution",
                "external_tenant_ref": "acme-distribution",
                "organisation_ref": "org-acme",
            },
            "webhook_api": {
                "integration_owner_contact": "integration@example.test",
            },
        },
        "validation": _validation(),
    }
    params.update(overrides)
    return build_draft_save_audit_evidence(**params)


def test_evidence_includes_actor_role_external_refs_and_correlation_id():
    evidence = _evidence()

    assert evidence["actor_ref"] == "operator-1"
    assert evidence["actor_role"] == "PLATFORM_ADMIN"
    assert evidence["permission_scope"] == {
        "route_family": "admin_onboarding",
        "role_family": "platform_operator",
        "external_scope": {
            "external_tenant_ref": "acme-distribution",
            "organisation_ref": "org-acme",
            "producer_ref": "prod-acme",
            "campaign_code": "CAMP-ACME",
        },
    }
    assert evidence["external_scope"] == {
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
        "producer_ref": "prod-acme",
        "campaign_code": "CAMP-ACME",
    }
    assert evidence["draft_ref"] == "draft_001"
    assert evidence["operation_type"] == "ONBOARDING_DRAFT_CREATE"
    assert evidence["correlation_id"] == "corr-123"
    assert evidence["no_live_action_confirmed"] is True


def test_evidence_uses_idempotency_hash_reference_not_raw_key():
    evidence = _evidence(idempotency_reference="hashed-idempotency-reference")
    rendered = json.dumps(evidence, sort_keys=True)

    assert evidence["idempotency_reference"] == "hashed-idempotency-reference"
    assert "draft-save-key-1" not in rendered
    assert "raw-idempotency-key" not in rendered


def test_evidence_includes_before_and_after_hashes_without_raw_sensitive_payloads():
    evidence = _evidence(
        current_sections={
            "webhook_api": {
                "callback_url_placeholder": "https://example.test/webhooks",
                "api_key": "SECRET-API-KEY",
                "client_secret": "SECRET-CLIENT",
            }
        }
    )
    rendered = json.dumps(evidence, sort_keys=True).lower()

    assert evidence["before_state_hash"] == EMPTY_STATE_HASH
    assert len(evidence["after_state_hash"]) == 64
    assert "secret-api-key" not in rendered
    assert "secret-client" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered
    assert "secret_or_credential" in evidence["redaction_summary"]["categories"]


def test_evidence_detects_changed_sections_against_prior_safe_state():
    evidence = _evidence(
        prior_sections={
            "company": {
                "organisation_name": "Acme Distribution",
                "external_tenant_ref": "acme-distribution",
                "organisation_ref": "org-acme",
            },
            "webhook_api": {
                "integration_owner_contact": "old@example.test",
            },
        },
        current_sections={
            "company": {
                "organisation_name": "Acme Distribution",
                "external_tenant_ref": "acme-distribution",
                "organisation_ref": "org-acme",
            },
            "webhook_api": {
                "integration_owner_contact": "integration@example.test",
            },
        },
    )

    assert evidence["changed_sections"] == ["webhook_api"]


def test_evidence_summarises_validation_readiness_and_redactions():
    evidence = _evidence()

    assert evidence["validation_summary"] == {
        "status": "MISSING_EVIDENCE",
        "safe_error_count": 0,
        "missing_evidence_count": 1,
        "blocker_count": 0,
    }
    assert evidence["readiness_summary"] == {
        "overall_status": "GO_LIVE_DISABLED",
        "ready_count": 2,
        "blocked_count": 0,
        "missing_evidence_count": 1,
        "go_live_disabled_count": 8,
        "total_count": 8,
    }
    assert evidence["redaction_summary"] == {
        "categories": ["SECRETS_REDACTED", "TENANT_CODE_INTERNAL"],
        "redacted": True,
    }


def test_evidence_does_not_include_tenant_code_or_money_and_webhook_internals():
    evidence = _evidence(
        external_scope={
            "external_tenant_ref": "acme-distribution",
            "organisation_ref": "org-acme",
            "tenant_code": "INTERNAL-FNB",
        },
        current_sections={
            "company": {
                "organisation_name": "Acme Distribution",
                "tenant_code": "INTERNAL-FNB",
                "wallet_account": "unsafe-wallet",
                "settlement_batch": "unsafe-settlement",
                "fulfilment_payload": "unsafe-fulfilment",
                "retry_payload": "unsafe-retry",
                "money_movement_amount": "1000.00",
                "deliver_webhook": True,
                "provider_payload": {"raw_status": "unsafe"},
            }
        },
    )
    rendered = json.dumps(evidence, sort_keys=True).lower()

    assert evidence["external_scope"] == {
        "external_tenant_ref": "acme-distribution",
        "organisation_ref": "org-acme",
    }
    assert "internal-fnb" not in rendered
    assert '"tenant_code":' not in rendered
    assert "unsafe-wallet" not in rendered
    assert "unsafe-settlement" not in rendered
    assert "unsafe-fulfilment" not in rendered
    assert "unsafe-retry" not in rendered
    assert "1000.00" not in rendered
    assert "provider_payload" not in rendered
    assert "raw_status" not in rendered
    assert "deliver_webhook" not in rendered
    assert "money_movement_internal" in evidence["redaction_summary"]["categories"]
    assert "webhook_internal" in evidence["redaction_summary"]["categories"]


def test_audit_link_fields_are_reference_only_and_do_not_dispatch():
    evidence = _evidence()
    fields = build_draft_save_audit_link_fields(
        draft_id="draft-uuid",
        evidence=evidence,
        idempotency_id="idem-uuid",
    )
    rendered = json.dumps(fields, sort_keys=True)

    assert fields["draft_id"] == "draft-uuid"
    assert fields["action_type"] == "ONBOARDING_DRAFT_CREATE"
    assert fields["action_status"] == "SUCCESS"
    assert fields["evidence_type"] == "DRAFT_SAVE_AUDIT_EVIDENCE"
    assert fields["audit_ref"] is None
    assert fields["event_ref"] is None
    assert fields["idempotency_id"] == "idem-uuid"
    assert fields["evidence_summary"]["dispatch"] == {
        "event_dispatched": False,
        "webhook_dispatched": False,
        "event_ref": None,
    }
    assert "dispatch_webhook" not in rendered
    assert "enqueue_event" not in rendered


def test_helper_module_exposes_no_dispatch_or_live_action_functions():
    import services.onboarding.onboarding_draft_audit_evidence_service as service

    public_names = {
        name
        for name in dir(service)
        if not name.startswith("_") and callable(getattr(service, name))
    }

    forbidden_parts = (
        "dispatch",
        "webhook",
        "replay",
        "repair",
        "credential",
        "invite",
        "publish",
        "fund",
        "fulfil",
        "settle",
        "retry",
        "wallet",
        "go_live",
        "money",
    )
    for name in public_names:
        for forbidden in forbidden_parts:
            assert forbidden not in name
