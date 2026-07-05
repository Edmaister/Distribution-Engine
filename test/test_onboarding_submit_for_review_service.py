from __future__ import annotations

import json

import pytest

from services.onboarding import onboarding_submit_for_review_service as service
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
        "draft_version": 2,
        "external_tenant_ref": "ext-tenant-1",
        "organisation_ref": "org-1",
        "status": "DRAFT_CREATED",
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


def _request_hash(*, validation=None, expected_draft_version=2):
    payload = service.build_submit_for_review_request_payload(
        draft_ref="draft_001",
        expected_draft_version=expected_draft_version,
        validation=validation or _valid_validation(),
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
        return {
            **self.draft,
            "status": service.TARGET_REVIEW_STATUS,
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


async def _submit(**overrides):
    params = {
        "draft_ref": "draft_001",
        "expected_draft_version": 2,
        "idempotency_key": "review-key-1",
        "actor_ref": "operator-1",
        "actor_role": "SYSTEM_ADMIN",
        "validation": _valid_validation(),
        "correlation_id": "corr-1",
    }
    params.update(overrides)
    return await service.submit_onboarding_draft_for_review(**params)


@pytest.mark.asyncio
async def test_submit_for_review_transitions_valid_draft(monkeypatch):
    stub = DraftRepoStub(draft=_DEFAULT_DRAFT)
    _patch_repo(monkeypatch, stub)

    result = await _submit()
    rendered = json.dumps(result, sort_keys=True)

    assert result["status"] == service.RESULT_SUBMITTED_FOR_REVIEW
    assert result["previous_status"] == "DRAFT_CREATED"
    assert result["draft_status"] == service.TARGET_REVIEW_STATUS
    assert result["draft_version"] == 3
    assert result["no_live_action_confirmed"] is True
    assert "tenant_code" not in rendered
    assert "internal-tenant" not in rendered
    assert "api_key" not in rendered
    assert stub.updated_kwargs["status"] == service.TARGET_REVIEW_STATUS
    assert stub.updated_kwargs["expected_draft_version"] == 2
    assert stub.updated_kwargs["metadata"]["review_transition"]["operation_type"] == (
        service.OPERATION_SUBMIT_FOR_REVIEW
    )
    assert stub.recorded_idempotency_kwargs["result_status"] == "SUCCESS"
    assert stub.recorded_idempotency_kwargs["operation_type"] == (
        service.OPERATION_SUBMIT_FOR_REVIEW
    )
    assert stub.recorded_idempotency_kwargs["idempotency_key_hash"] == (
        hash_idempotency_key("review-key-1")
    )
    assert stub.recorded_idempotency_kwargs["scope_hash"] == build_scope_hash(
        actor_ref="operator-1",
        external_tenant_ref="ext-tenant-1",
        operation_type=service.OPERATION_SUBMIT_FOR_REVIEW,
        draft_ref="draft_001",
    )
    assert "review-key-1" not in json.dumps(stub.recorded_idempotency_kwargs)
    assert result["audit_evidence_status"] == "RECORDED_REFERENCE"
    assert result["audit_evidence_ref"] == "SUBMIT_FOR_REVIEW_AUDIT_EVIDENCE"
    assert result["audit_link_ref"] == "audit-link-uuid"
    assert stub.audit_link_kwargs["action_type"] == (
        service.OPERATION_SUBMIT_FOR_REVIEW
    )
    assert stub.audit_link_kwargs["action_status"] == "SUCCESS"
    assert stub.audit_link_kwargs["evidence_type"] == (
        "SUBMIT_FOR_REVIEW_AUDIT_EVIDENCE"
    )
    assert stub.audit_link_kwargs["audit_ref"] is None
    assert stub.audit_link_kwargs["event_ref"] is None
    assert stub.audit_link_kwargs["idempotency_id"] == "idem-uuid"
    assert stub.audit_link_kwargs["actor_ref"] == "operator-1"
    assert stub.audit_link_kwargs["actor_role"] == "SYSTEM_ADMIN"
    assert stub.audit_link_kwargs["correlation_id"] == "corr-1"
    assert stub.audit_link_kwargs["changed_sections"] == [
        "draft_status",
        "draft_version",
    ]
    assert stub.audit_link_kwargs["evidence_summary"]["dispatch"] == {
        "event_dispatched": False,
        "webhook_dispatched": False,
        "event_ref": None,
    }
    rendered_audit = json.dumps(stub.audit_link_kwargs, sort_keys=True).lower()
    assert "tenant_code" not in rendered_audit
    assert "internal-tenant" not in rendered_audit
    assert "review-key-1" not in rendered_audit


@pytest.mark.asyncio
async def test_submit_for_review_rejects_missing_draft(monkeypatch):
    stub = DraftRepoStub(draft=None)
    _patch_repo(monkeypatch, stub)

    result = await _submit()

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_DRAFT_NOT_FOUND
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_submit_for_review_rejects_invalid_source_status(monkeypatch):
    stub = DraftRepoStub(draft=_draft(status="DISCARDED"))
    _patch_repo(monkeypatch, stub)

    result = await _submit()

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_INVALID_STATE
    assert result["error"]["current_status"] == "DISCARDED"
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_submit_for_review_rejects_stale_version(monkeypatch):
    stub = DraftRepoStub(draft=_DEFAULT_DRAFT, stale=True)
    _patch_repo(monkeypatch, stub)

    result = await _submit(expected_draft_version=1)

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_STALE_DRAFT
    assert stub.updated_kwargs["expected_draft_version"] == 1
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_submit_for_review_replays_same_idempotency_payload(monkeypatch):
    existing_reference = {
        "idempotency_key_hash": hash_idempotency_key("review-key-1"),
        "scope_hash": build_scope_hash(
            actor_ref="operator-1",
            external_tenant_ref="ext-tenant-1",
            operation_type=service.OPERATION_SUBMIT_FOR_REVIEW,
            draft_ref="draft_001",
        ),
        "request_hash": _request_hash(),
        "result_status": "SUCCESS",
        "response_hash": "safe-response-hash",
    }
    stub = DraftRepoStub(
        draft=_draft(status=service.TARGET_REVIEW_STATUS),
        existing_reference=existing_reference,
    )
    _patch_repo(monkeypatch, stub)

    result = await _submit()

    assert result["status"] == service.RESULT_REPLAYED
    assert result["draft_status"] == service.TARGET_REVIEW_STATUS
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_submit_for_review_rejects_idempotency_conflict(monkeypatch):
    existing_reference = {
        "idempotency_key_hash": hash_idempotency_key("review-key-1"),
        "scope_hash": build_scope_hash(
            actor_ref="operator-1",
            external_tenant_ref="ext-tenant-1",
            operation_type=service.OPERATION_SUBMIT_FOR_REVIEW,
            draft_ref="draft_001",
        ),
        "request_hash": "different-request-hash",
        "result_status": "SUCCESS",
    }
    stub = DraftRepoStub(draft=_DEFAULT_DRAFT, existing_reference=existing_reference)
    _patch_repo(monkeypatch, stub)

    result = await _submit()

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_IDEMPOTENCY_CONFLICT
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_submit_for_review_rejects_validation_blockers(monkeypatch):
    stub = DraftRepoStub(draft=_draft(status="VALIDATION_FAILED"))
    _patch_repo(monkeypatch, stub)
    validation = _valid_validation(
        validation_result={"status": "BLOCKED"},
        blockers=[{"code": "UNSAFE_OPERATION"}],
        safe_errors=[{"code": "UNSAFE_OPERATION"}],
    )

    result = await _submit(validation=validation)

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_VALIDATION_BLOCKED
    assert stub.updated_kwargs is None
    assert stub.recorded_idempotency_kwargs is None
    assert stub.audit_link_kwargs is None


@pytest.mark.asyncio
async def test_submit_for_review_rejects_adjacent_role(monkeypatch):
    stub = DraftRepoStub(draft=_DEFAULT_DRAFT)
    _patch_repo(monkeypatch, stub)

    result = await _submit(actor_role="DISTRIBUTOR_ADMIN")

    assert result["status"] == service.RESULT_REJECTED
    assert result["error"]["code"] == service.ERROR_PERMISSION_DENIED_SUBMIT
    assert stub.updated_kwargs is None
    assert stub.audit_link_kwargs is None
    assert stub.recorded_idempotency_kwargs is None


@pytest.mark.asyncio
async def test_submit_for_review_result_does_not_expose_live_or_money_fields(
    monkeypatch,
):
    stub = DraftRepoStub(
        draft=_draft(
            status="DRAFT_UPDATED",
            tenant_code="tenant-internal",
            wallet_ref="wallet-internal",
            settlement_ref="settlement-internal",
        )
    )
    _patch_repo(monkeypatch, stub)

    result = await _submit()
    rendered = json.dumps(result, sort_keys=True).lower()

    assert result["status"] == service.RESULT_SUBMITTED_FOR_REVIEW
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
