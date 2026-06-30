import json

from services.onboarding.onboarding_draft_idempotency_service import (
    REASON_MISSING_IDEMPOTENCY_KEY,
    REASON_UNSUPPORTED_OPERATION,
    STATUS_CONFLICT_DIFFERENT_PAYLOAD,
    STATUS_INVALID_IDEMPOTENCY_KEY,
    STATUS_NEW_REQUEST,
    STATUS_REPLAY_SAME_PAYLOAD,
    build_scope_hash,
    canonical_payload,
    evaluate_draft_idempotency,
    hash_idempotency_key,
    hash_payload,
)


def _decision(existing_reference=None, **overrides):
    params = {
        "idempotency_key": "draft-key-123",
        "actor_ref": "operator-1",
        "external_tenant_ref": "ext-tenant-1",
        "operation_type": "ONBOARDING_DRAFT_UPDATE",
        "draft_ref": "draft-ref-1",
        "request_payload": {
            "organisation_ref": "org-1",
            "section": "company",
            "status": "DRAFT",
        },
        "existing_reference": existing_reference,
    }
    params.update(overrides)
    return evaluate_draft_idempotency(**params)


def test_new_request_returns_repository_safe_hash_fields_only():
    decision = _decision()

    fields = decision.repository_fields()
    rendered = json.dumps(fields, sort_keys=True)

    assert decision.status == STATUS_NEW_REQUEST
    assert fields["idempotency_key_hash"] == hash_idempotency_key("draft-key-123")
    assert fields["scope_hash"] == build_scope_hash(
        actor_ref="operator-1",
        external_tenant_ref="ext-tenant-1",
        operation_type="ONBOARDING_DRAFT_UPDATE",
        draft_ref="draft-ref-1",
    )
    assert fields["request_hash"] == hash_payload(
        {
            "organisation_ref": "org-1",
            "section": "company",
            "status": "DRAFT",
        }
    )
    assert "draft-key-123" not in rendered
    assert "organisation_ref" not in rendered
    assert "tenant_code" not in rendered


def test_same_key_same_payload_is_replay():
    first = _decision()
    existing = {
        **first.repository_fields(),
        "result_status": "SUCCESS",
        "response_hash": "stored-response-hash",
    }

    replay = _decision(existing_reference=existing)

    assert replay.status == STATUS_REPLAY_SAME_PAYLOAD
    assert replay.is_replay
    assert replay.existing_result_status == "SUCCESS"
    assert replay.existing_response_hash == "stored-response-hash"


def test_same_key_different_payload_is_conflict():
    first = _decision()
    existing = {
        **first.repository_fields(),
        "result_status": "SUCCESS",
    }

    conflict = _decision(
        existing_reference=existing,
        request_payload={"organisation_ref": "org-1", "section": "company", "status": "READY"},
    )

    assert conflict.status == STATUS_CONFLICT_DIFFERENT_PAYLOAD
    assert conflict.is_conflict
    assert conflict.existing_result_status == "SUCCESS"


def test_same_key_with_different_actor_is_separate_scope():
    first = _decision()
    existing = {
        **first.repository_fields(),
        "result_status": "SUCCESS",
    }

    scoped = _decision(existing_reference=existing, actor_ref="operator-2")

    assert scoped.status == STATUS_NEW_REQUEST
    assert scoped.scope_hash != existing["scope_hash"]


def test_same_key_with_different_external_tenant_is_separate_scope():
    first = _decision()
    existing = {
        **first.repository_fields(),
        "result_status": "SUCCESS",
    }

    scoped = _decision(existing_reference=existing, external_tenant_ref="ext-tenant-2")

    assert scoped.status == STATUS_NEW_REQUEST
    assert scoped.scope_hash != existing["scope_hash"]


def test_same_key_with_different_draft_operation_is_separate_scope():
    first = _decision()
    existing = {
        **first.repository_fields(),
        "result_status": "SUCCESS",
    }

    scoped = _decision(
        existing_reference=existing,
        operation_type="ONBOARDING_DRAFT_VALIDATE",
    )

    assert scoped.status == STATUS_NEW_REQUEST
    assert scoped.scope_hash != existing["scope_hash"]


def test_payload_hash_is_deterministic_for_key_order():
    left = {"b": 2, "a": {"y": True, "x": ["one", "two"]}}
    right = {"a": {"x": ["one", "two"], "y": True}, "b": 2}

    assert canonical_payload(left) == canonical_payload(right)
    assert hash_payload(left) == hash_payload(right)


def test_sensitive_payload_values_are_not_returned():
    decision = _decision(
        request_payload={
            "webhook_api": {
                "api_key": "SECRET-KEY-123",
                "client_secret": "CLIENT-SECRET-456",
            }
        }
    )

    rendered = json.dumps(decision.__dict__, sort_keys=True)

    assert decision.status == STATUS_NEW_REQUEST
    assert "SECRET-KEY-123" not in rendered
    assert "CLIENT-SECRET-456" not in rendered
    assert "api_key" not in rendered
    assert "client_secret" not in rendered


def test_blank_idempotency_key_is_invalid_without_raw_value():
    decision = _decision(idempotency_key="  ")

    assert decision.status == STATUS_INVALID_IDEMPOTENCY_KEY
    assert decision.reason == REASON_MISSING_IDEMPOTENCY_KEY
    assert decision.repository_fields() == {}


def test_live_action_operation_is_rejected_as_unsupported():
    decision = _decision(operation_type="ACTIVATE_GO_LIVE")

    rendered = json.dumps(decision.__dict__, sort_keys=True)

    assert decision.status == STATUS_INVALID_IDEMPOTENCY_KEY
    assert decision.reason == REASON_UNSUPPORTED_OPERATION
    assert decision.repository_fields() == {}
    assert "ACTIVATE_GO_LIVE" not in rendered
