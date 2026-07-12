from __future__ import annotations

import json

import pytest

from services.onboarding import onboarding_review_decision_service as service
from services.onboarding.onboarding_draft_idempotency_service import (
    build_scope_hash,
    hash_idempotency_key,
    hash_payload,
)
from services.onboarding.onboarding_draft_repository import StaleDraftVersionError


def _draft(**overrides):
    draft = {
        "draft_id": "draft-uuid",
        "draft_ref": "draft_001",
        "draft_version": 4,
        "external_tenant_ref": "ext-tenant-1",
        "organisation_ref": "org-1",
        "status": service.SOURCE_READY_FOR_REVIEW,
        "tenant_code": "internal-tenant",
    }
    draft.update(overrides)
    return draft


def _valid_validation(**overrides):
    validation = {
        "validation_result": {
            "status": "VALID",
            "validated_scope": {"external_tenant_ref": "ext-tenant-1"},
        },
        "readiness_preview": {"status": "READY_FOR_REVIEW"},
        "blockers": [],
        "missing_evidence": [],
        "safe_errors": [],
        "warnings": [{"code": "GO_LIVE_DISABLED"}],
        "redactions": ["secret_or_credential"],
        "no_persistence_confirmed": True,
    }
    validation.update(overrides)
    return validation


def _request_hash(
    *,
    validation=None,
    expected_draft_version=4,
    review_outcome=service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW,
    reason_category="OPERATOR_REVIEW",
    reason="Evidence is complete enough for internal review.",
):
    payload = service.build_review_decision_request_payload(
        draft_ref="draft_001",
        expected_draft_version=expected_draft_version,
        review_outcome=review_outcome,
        reason_category=reason_category,
        reason=reason,
        validation=validation or _valid_validation(),
        target_status=service.target_status_for_review_outcome(review_outcome),
    )
    return hash_payload(payload)


_DEFAULT_DRAFT = object()


class DraftRepoStub:
    def __init__(self, *, draft=_DEFAULT_DRAFT, existing_reference=None, stale=False):
        self.draft = _draft() if draft is _DEFAULT_DRAFT else draft
        self.existing_reference = existing_reference
        self.stale = stale
        self.updated_kwargs = None
        self.idempotency_lookup_kwargs = None
        self.recorded_idempotency_kwargs = None
        self.audit_link_kwargs = None

    async def get_draft_by_ref(self, draft_ref):
        assert draft_ref == "draft_001"
        return self.draft

    async def get_idempotency_reference(self, **kwargs):
        self.idempotency_lookup_kwargs = kwargs
        return self.existing_reference

    async def update_draft_metadata_or_status(self, **kwargs):
        self.updated_kwargs = kwargs
        if self.stale:
            raise StaleDraftVersionError("stale")
        status = kwargs.get("status") or self.draft["status"]
        return {
            **self.draft,
            "status": status,
            "draft_version": self.draft["draft_version"] + 1,
        }

    async def record_idempotency_reference(self, **kwargs):
        self.recorded_idempotency_kwargs = kwargs
        return {
            "idempotency_id": "idem-uuid",
            **kwargs,
        }

    async def create_audit_link_reference(self, **kwargs):
        self.audit_link_kwargs = kwargs
        return {
            "audit_link_id": "audit-link-uuid",
            **kwargs,
        }


def _patch_repo(monkeypatch, stub):
    monkeypatch.setattr(service.draft_repo, "get_draft_by_ref", stub.get_draft_by_ref)
    monkeypatch.setattr(
        service.draft_repo,
        "get_idempotency_reference",
        stub.get_idempotency_reference,
    )
    monkeypatch.setattr(
        service.draft_repo,
        "update_draft_metadata_or_status",
        stub.update_draft_metadata_or_status,
    )
    monkeypatch.setattr(
        service.draft_repo,
        "record_idempotency_reference",
        stub.record_idempotency_reference,
    )
    monkeypatch.setattr(
        service.draft_repo,
        "create_audit_link_reference",
        stub.create_audit_link_reference,
    )


async def _review(**overrides):
    params = {
        "draft_ref": "draft_001",
        "expected_draft_version": 4,
        "idempotency_key": "decision-key-1",
        "actor_ref": "operator-1",
        "actor_role": "SYSTEM_ADMIN",
        "review_outcome": service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW,
        "reason_category": "OPERATOR_REVIEW",
        "reason": "Evidence is complete enough for internal review.",
        "validation": _valid_validation(),
        "correlation_id": "corr-1",
    }
    params.update(overrides)
    return await service.record_onboarding_draft_review_decision(**params)


@pytest.mark.asyncio
async def test_review_decision_records_internal_approval_as_metadata_only(
    monkeypatch,
):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review()
    rendered = json.dumps(result, sort_keys=True).lower()

    assert result["status"] == service.RESULT_REVIEW_DECISION_RECORDED
    assert result["previous_status"] == service.SOURCE_READY_FOR_REVIEW
    assert result["draft_status"] == service.SOURCE_READY_FOR_REVIEW
    assert result["review_outcome"] == service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW
    assert result["approval_to_launch"] is False
    assert result["go_live_enabled"] is False
    assert result["audit_evidence_ref"] == "REVIEW_DECISION_AUDIT_EVIDENCE"
    assert result["audit_link_ref"] == "audit-link-uuid"
    assert result["audit_evidence_status"] == "RECORDED_REFERENCE"
    assert result["no_live_action_confirmed"] is True
    assert "tenant_code" not in rendered
    assert "internal-tenant" not in rendered
    assert "decision-key-1" not in rendered
    assert "evidence is complete" not in rendered

    assert stub.updated_kwargs["status"] == service.SOURCE_READY_FOR_REVIEW
    assert stub.updated_kwargs["expected_draft_version"] == 4
    decision_metadata = stub.updated_kwargs["metadata"]["review_decision"]
    assert decision_metadata["operation_type"] == service.OPERATION_REVIEW_DECISION
    assert decision_metadata["review_outcome"] == (
        service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW
    )
    assert decision_metadata["target_status"] == service.SOURCE_READY_FOR_REVIEW
    assert decision_metadata["no_live_action_confirmed"] is True
    assert "reason_hash" in decision_metadata
    assert "Evidence is complete" not in json.dumps(decision_metadata)

    assert stub.recorded_idempotency_kwargs["result_status"] == "SUCCESS"
    assert stub.recorded_idempotency_kwargs["operation_type"] == (
        service.OPERATION_REVIEW_DECISION
    )
    assert stub.recorded_idempotency_kwargs["idempotency_key_hash"] == (
        hash_idempotency_key("decision-key-1")
    )
    assert stub.recorded_idempotency_kwargs["scope_hash"] == build_scope_hash(
        actor_ref="operator-1",
        external_tenant_ref="ext-tenant-1",
        operation_type=service.OPERATION_REVIEW_DECISION,
        draft_ref="draft_001",
    )
    assert "decision-key-1" not in json.dumps(stub.recorded_idempotency_kwargs)
    assert stub.audit_link_kwargs["action_type"] == service.OPERATION_REVIEW_DECISION
    assert stub.audit_link_kwargs["action_status"] == "SUCCESS"
    assert stub.audit_link_kwargs["evidence_type"] == (
        "REVIEW_DECISION_AUDIT_EVIDENCE"
    )
    assert stub.audit_link_kwargs["audit_ref"] is None
    assert stub.audit_link_kwargs["event_ref"] is None
    assert stub.audit_link_kwargs["idempotency_id"] == "idem-uuid"
    assert stub.audit_link_kwargs["evidence_summary"]["review_outcome"] == (
        service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW
    )
    assert stub.audit_link_kwargs["evidence_summary"]["reason_reference"]
    assert stub.audit_link_kwargs["evidence_summary"]["dispatch"] == {
        "event_dispatched": False,
        "webhook_dispatched": False,
        "event_ref": None,
    }
    rendered_audit = json.dumps(stub.audit_link_kwargs, sort_keys=True).lower()
    assert "decision-key-1" not in rendered_audit
    assert "evidence is complete" not in rendered_audit
    assert "tenant_code" not in rendered_audit
    assert "internal-tenant" not in rendered_audit


@pytest.mark.asyncio
async def test_review_decision_records_schema_backed_blocked_outcome(monkeypatch):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(
        review_outcome=service.OUTCOME_BLOCKED,
        reason_category="MISSING_POLICY_SIGNOFF",
        reason="Policy sign-off must be completed before this can continue.",
    )

    assert result["status"] == service.RESULT_REVIEW_DECISION_RECORDED
    assert result["draft_status"] == service.TARGET_BLOCKED
    assert result["review_outcome"] == service.OUTCOME_BLOCKED
    assert stub.updated_kwargs["status"] == service.TARGET_BLOCKED
    assert stub.updated_kwargs["metadata"]["review_decision"]["review_outcome"] == (
        service.OUTCOME_BLOCKED
    )
    assert stub.audit_link_kwargs["evidence_summary"]["review_status"] == (
        service.TARGET_BLOCKED
    )


@pytest.mark.asyncio
async def test_review_decision_rejects_unsupported_schema_outcome(monkeypatch):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(review_outcome=service.OUTCOME_REJECTED)

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_UNSUPPORTED_SCHEMA_STATE
    assert result["review_outcome"] == service.OUTCOME_REJECTED
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_changes_requested_until_schema_backed(
    monkeypatch,
):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(review_outcome=service.OUTCOME_CHANGES_REQUESTED)

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_UNSUPPORTED_SCHEMA_STATE
    assert result["review_outcome"] == service.OUTCOME_CHANGES_REQUESTED
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_unknown_review_outcome(monkeypatch):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(review_outcome="approve and launch")

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_UNSUPPORTED_REVIEW_OUTCOME
    assert result["review_outcome"] == "APPROVE_AND_LAUNCH"
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_missing_draft(monkeypatch):
    stub = DraftRepoStub(draft=None)
    _patch_repo(monkeypatch, stub)

    result = await _review()

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_DRAFT_NOT_FOUND
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.parametrize(
    "source_status",
    [
        "DRAFT_CREATED",
        "DRAFT_UPDATED",
        "VALIDATION_FAILED",
        "BLOCKED",
        "DISCARDED",
    ],
)
@pytest.mark.asyncio
async def test_review_decision_rejects_all_non_review_source_statuses(
    monkeypatch,
    source_status,
):
    stub = DraftRepoStub(draft=_draft(status=source_status))
    _patch_repo(monkeypatch, stub)

    result = await _review()

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_INVALID_STATE
    assert result["error"]["current_status"] == source_status
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_missing_external_scope(monkeypatch):
    stub = DraftRepoStub(draft=_draft(external_tenant_ref=""))
    _patch_repo(monkeypatch, stub)

    result = await _review()

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_VALIDATION_BLOCKED
    assert stub.idempotency_lookup_kwargs is None
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_stale_version(monkeypatch):
    stub = DraftRepoStub(stale=True)
    _patch_repo(monkeypatch, stub)

    result = await _review(expected_draft_version=3)

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_STALE_DRAFT
    assert stub.updated_kwargs["expected_draft_version"] == 3
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_replays_same_idempotency_payload(monkeypatch):
    existing_reference = {
        "idempotency_key_hash": hash_idempotency_key("decision-key-1"),
        "scope_hash": build_scope_hash(
            actor_ref="operator-1",
            external_tenant_ref="ext-tenant-1",
            operation_type=service.OPERATION_REVIEW_DECISION,
            draft_ref="draft_001",
        ),
        "request_hash": _request_hash(),
        "result_status": "SUCCESS",
        "response_hash": "safe-response-hash",
    }
    stub = DraftRepoStub(existing_reference=existing_reference)
    _patch_repo(monkeypatch, stub)

    result = await _review()

    assert result["status"] == service.RESULT_REPLAYED
    assert result["draft_status"] == service.SOURCE_READY_FOR_REVIEW
    assert result["review_outcome"] == service.OUTCOME_APPROVED_FOR_INTERNAL_REVIEW
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_idempotency_conflict(monkeypatch):
    existing_reference = {
        "idempotency_key_hash": hash_idempotency_key("decision-key-1"),
        "scope_hash": build_scope_hash(
            actor_ref="operator-1",
            external_tenant_ref="ext-tenant-1",
            operation_type=service.OPERATION_REVIEW_DECISION,
            draft_ref="draft_001",
        ),
        "request_hash": "different-request-hash",
        "result_status": "SUCCESS",
    }
    stub = DraftRepoStub(existing_reference=existing_reference)
    _patch_repo(monkeypatch, stub)

    result = await _review()

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_IDEMPOTENCY_CONFLICT
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_invalid_idempotency_key(monkeypatch):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(idempotency_key="")

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_VALIDATION_BLOCKED
    assert stub.idempotency_lookup_kwargs is None
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_validation_blockers(monkeypatch):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)
    validation = _valid_validation(
        validation_result={"status": "BLOCKED"},
        blockers=[{"code": "UNSAFE_OPERATION"}],
        safe_errors=[{"code": "UNSAFE_OPERATION"}],
    )

    result = await _review(validation=validation)

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_VALIDATION_BLOCKED
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.parametrize(
    ("validation", "expected_message"),
    [
        (
            _valid_validation(missing_evidence=[{"code": "MISSING_SIGNOFF"}]),
            "Missing evidence prevents review decision.",
        ),
        (
            _valid_validation(safe_errors=[{"code": "UNSAFE_FIELD"}]),
            "Unsafe or permission-limited validation evidence prevents review decision.",
        ),
        (
            _valid_validation(safe_errors=["unsafe"]),
            "Validation safe errors prevent review decision.",
        ),
        (
            _valid_validation(readiness_preview={"status": "PERMISSION_LIMITED"}),
            "Readiness preview prevents review decision.",
        ),
    ],
)
@pytest.mark.asyncio
async def test_review_decision_rejects_validation_and_readiness_blocker_shapes(
    monkeypatch,
    validation,
    expected_message,
):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(validation=validation)

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_VALIDATION_BLOCKED
    assert result["error"]["message"] == expected_message
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_adjacent_role(monkeypatch):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(actor_role="DISTRIBUTOR_ADMIN")

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_PERMISSION_DENIED_REVIEW
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_rejects_missing_reason(monkeypatch):
    stub = DraftRepoStub()
    _patch_repo(monkeypatch, stub)

    result = await _review(reason="")

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_VALIDATION_BLOCKED
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_review_decision_result_does_not_expose_live_or_money_fields(
    monkeypatch,
):
    stub = DraftRepoStub(
        draft=_draft(
            tenant_code="tenant-internal",
            wallet_ref="wallet-internal",
            settlement_ref="settlement-internal",
        )
    )
    _patch_repo(monkeypatch, stub)

    result = await _review()
    rendered = json.dumps(result, sort_keys=True).lower()
    rendered_update = json.dumps(stub.updated_kwargs, sort_keys=True).lower()

    assert result["status"] == service.RESULT_REVIEW_DECISION_RECORDED
    forbidden = [
        "tenant_code",
        "tenant-internal",
        "wallet_ref",
        "settlement_ref",
        "webhook_delivery",
        "funding_ref",
        "fulfilment_ref",
        "retry_ref",
        "go_live_token",
    ]
    assert all(term not in rendered for term in forbidden)
    assert "decision-key-1" not in rendered_update
    assert "policy sign-off" not in rendered_update
