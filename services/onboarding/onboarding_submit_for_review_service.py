from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from services.onboarding import onboarding_draft_repository as draft_repo
from services.onboarding.onboarding_draft_audit_evidence_service import (
    build_submit_for_review_audit_evidence,
    build_submit_for_review_audit_link_fields,
)
from services.onboarding.onboarding_draft_idempotency_service import (
    STATUS_CONFLICT_DIFFERENT_PAYLOAD,
    STATUS_INVALID_IDEMPOTENCY_KEY,
    STATUS_REPLAY_SAME_PAYLOAD,
    evaluate_draft_idempotency,
    hash_payload,
)
from services.onboarding.onboarding_draft_validation_service import (
    ERROR_PERMISSION_DENIED,
    ERROR_UNSAFE_FIELD,
    ERROR_UNSAFE_OPERATION,
    VALIDATION_VALID,
)

OPERATION_SUBMIT_FOR_REVIEW: Final = "ONBOARDING_DRAFT_SUBMIT_FOR_REVIEW"
TARGET_REVIEW_STATUS: Final = "READY_FOR_REVIEW"

STATUS_DRAFT_CREATED: Final = "DRAFT_CREATED"
STATUS_DRAFT_UPDATED: Final = "DRAFT_UPDATED"
STATUS_VALIDATION_FAILED: Final = "VALIDATION_FAILED"

ELIGIBLE_SOURCE_STATUSES: Final = frozenset(
    {
        STATUS_DRAFT_CREATED,
        STATUS_DRAFT_UPDATED,
        STATUS_VALIDATION_FAILED,
    }
)
BLOCKED_SOURCE_STATUSES: Final = frozenset(
    {
        TARGET_REVIEW_STATUS,
        "SUBMITTED_FOR_REVIEW",
        "BLOCKED",
        "DISCARDED",
    }
)

RESULT_SUBMITTED_FOR_REVIEW: Final = "SUBMITTED_FOR_REVIEW"
RESULT_REPLAYED: Final = "REPLAYED"
RESULT_REJECTED: Final = "REJECTED"

ERROR_DRAFT_NOT_FOUND: Final = "DRAFT_NOT_FOUND"
ERROR_INVALID_STATE: Final = "INVALID_STATE"
ERROR_STALE_DRAFT: Final = "STALE_DRAFT"
ERROR_IDEMPOTENCY_CONFLICT: Final = "IDEMPOTENCY_CONFLICT"
ERROR_VALIDATION_BLOCKED: Final = "VALIDATION_BLOCKED"
ERROR_PERMISSION_DENIED_SUBMIT: Final = "PERMISSION_DENIED"
ERROR_UNSAFE_OPERATION_ATTEMPTED: Final = "UNSAFE_OPERATION"

ONBOARDING_ADMIN_ROLES: Final = frozenset(
    {
        "ADMIN",
        "SYSTEM_ADMIN",
        "DISTRIBUTION_ADMIN",
        "PLATFORM_ADMIN",
    }
)

NO_LIVE_ACTION_GUARDRAILS: Final = [
    "SUBMIT_FOR_REVIEW_ONLY",
    "NO_LIVE_MUTATION",
    "INTERNAL_TENANT_IDENTIFIER_ONLY",
    "NO_SECRET_EXPOSURE",
    "NO_APPROVAL_WORKFLOW",
    "NO_ACCOUNT_CREATION",
    "NO_INVITE_DELIVERY",
    "NO_CAMPAIGN_PUBLICATION",
    "NO_CREDENTIAL_LIFECYCLE",
    "NO_WEBHOOK_DISPATCH",
    "NO_AUDIT_EVENT_DISPATCH",
    "GO_LIVE_DISABLED",
    "NO_MONEY_MOVEMENT",
]


def build_submit_for_review_request_payload(
    *,
    draft_ref: str,
    expected_draft_version: int,
    validation: Mapping[str, Any],
    target_status: str = TARGET_REVIEW_STATUS,
) -> dict[str, Any]:
    validation_result = _as_mapping(validation.get("validation_result"))
    return {
        "draft_ref": _safe_text(draft_ref),
        "expected_draft_version": expected_draft_version,
        "operation_type": OPERATION_SUBMIT_FOR_REVIEW,
        "target_status": target_status,
        "validation_status": _safe_text(validation_result.get("status")),
    }


async def submit_onboarding_draft_for_review(
    *,
    draft_ref: str,
    expected_draft_version: int,
    idempotency_key: str,
    actor_ref: str,
    actor_role: str,
    validation: Mapping[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    role = _normalise_role(actor_role)
    if role not in ONBOARDING_ADMIN_ROLES:
        return _rejected(
            ERROR_PERMISSION_DENIED_SUBMIT,
            "Actor is not authorised to submit onboarding drafts for review.",
        )

    draft = await draft_repo.get_draft_by_ref(draft_ref)
    if not draft:
        return _rejected(
            ERROR_DRAFT_NOT_FOUND,
            "Draft reference is missing or unavailable.",
        )

    external_tenant_ref = _safe_text(draft.get("external_tenant_ref"))
    if not external_tenant_ref:
        return _rejected(
            ERROR_VALIDATION_BLOCKED,
            "Draft external scope is unavailable.",
        )

    request_payload = build_submit_for_review_request_payload(
        draft_ref=draft_ref,
        expected_draft_version=expected_draft_version,
        validation=validation,
    )
    initial_decision = evaluate_draft_idempotency(
        idempotency_key=idempotency_key,
        actor_ref=actor_ref,
        external_tenant_ref=external_tenant_ref,
        operation_type=OPERATION_SUBMIT_FOR_REVIEW,
        draft_ref=draft_ref,
        request_payload=request_payload,
    )
    if initial_decision.status == STATUS_INVALID_IDEMPOTENCY_KEY:
        return _rejected(
            ERROR_VALIDATION_BLOCKED,
            "A valid idempotency key is required for submit-for-review.",
        )

    existing_reference = await draft_repo.get_idempotency_reference(
        idempotency_key_hash=initial_decision.idempotency_key_hash or "",
        scope_hash=initial_decision.scope_hash or "",
    )
    decision = evaluate_draft_idempotency(
        idempotency_key=idempotency_key,
        actor_ref=actor_ref,
        external_tenant_ref=external_tenant_ref,
        operation_type=OPERATION_SUBMIT_FOR_REVIEW,
        draft_ref=draft_ref,
        request_payload=request_payload,
        existing_reference=existing_reference,
    )

    if decision.status == STATUS_REPLAY_SAME_PAYLOAD:
        return {
            **_base_response(),
            "status": RESULT_REPLAYED,
            "draft_ref": _safe_text(draft_ref),
            "draft_status": TARGET_REVIEW_STATUS,
            "idempotency_status": decision.status,
        }
    if decision.status == STATUS_CONFLICT_DIFFERENT_PAYLOAD:
        return _rejected(
            ERROR_IDEMPOTENCY_CONFLICT,
            "Idempotency key was reused with a different submit-for-review payload.",
            idempotency_status=decision.status,
        )

    current_status = _safe_text(draft.get("status")).upper()
    if current_status not in ELIGIBLE_SOURCE_STATUSES:
        return _rejected(
            ERROR_INVALID_STATE,
            "Draft cannot be submitted for review from its current state.",
            current_status=current_status or None,
        )

    validation_blocker = _validation_blocker(validation)
    if validation_blocker:
        return _rejected(
            ERROR_VALIDATION_BLOCKED,
            validation_blocker,
        )

    try:
        updated = await draft_repo.update_draft_metadata_or_status(
            draft_ref=draft_ref,
            expected_draft_version=expected_draft_version,
            status=TARGET_REVIEW_STATUS,
            metadata={
                "review_transition": {
                    "operation_type": OPERATION_SUBMIT_FOR_REVIEW,
                    "target_status": TARGET_REVIEW_STATUS,
                    "validation_status": VALIDATION_VALID,
                }
            },
            safe_summary={
                "review_transition": {
                    "previous_status": current_status,
                    "target_status": TARGET_REVIEW_STATUS,
                    "no_live_action_confirmed": True,
                }
            },
            updated_by_ref=actor_ref,
            correlation_id=correlation_id,
            redactions=_string_list(validation.get("redactions")),
        )
    except draft_repo.StaleDraftVersionError:
        return _rejected(
            ERROR_STALE_DRAFT,
            "Draft version is stale.",
            current_status=current_status,
        )

    response = {
        **_base_response(),
        "status": RESULT_SUBMITTED_FOR_REVIEW,
        "draft_ref": _safe_text(draft_ref),
        "previous_status": current_status,
        "draft_status": TARGET_REVIEW_STATUS,
        "draft_version": updated.get("draft_version"),
        "idempotency_status": decision.status,
        "validation_status": VALIDATION_VALID,
    }
    idempotency_fields = decision.repository_fields()
    idempotency_fields["draft_ref"] = _safe_text(draft_ref)
    idempotency_record = await draft_repo.record_idempotency_reference(
        **idempotency_fields,
        draft_id=_safe_text(updated.get("draft_id")) or None,
        result_status="SUCCESS",
        response_hash=hash_payload(response),
        correlation_id=correlation_id,
    )
    audit_evidence = build_submit_for_review_audit_evidence(
        actor_ref=actor_ref,
        actor_role=role,
        permission_scope={
            "route_family": "admin_onboarding",
            "role_family": "admin_operator",
        },
        prior_draft=draft,
        updated_draft=updated,
        action_status="SUCCESS",
        idempotency_reference=decision.idempotency_key_hash,
        correlation_id=correlation_id,
        validation=validation,
        target_status=TARGET_REVIEW_STATUS,
    )
    audit_link = await draft_repo.create_audit_link_reference(
        **build_submit_for_review_audit_link_fields(
            draft_id=_safe_text(updated.get("draft_id")) or "",
            evidence=audit_evidence,
            idempotency_id=_safe_text(idempotency_record.get("idempotency_id")) or None,
        )
    )
    response["audit_evidence_status"] = "RECORDED_REFERENCE"
    response["audit_evidence_ref"] = _safe_text(audit_link.get("evidence_type"))
    response["audit_link_ref"] = _safe_text(audit_link.get("audit_link_id"))
    return response


def _validation_blocker(validation: Mapping[str, Any]) -> str | None:
    validation_result = _as_mapping(validation.get("validation_result"))
    validation_status = _safe_text(validation_result.get("status")).upper()
    if validation_status != VALIDATION_VALID:
        return "Current validation evidence does not allow review."
    if _as_sequence(validation.get("blockers")):
        return "Validation blockers prevent review."
    if _as_sequence(validation.get("missing_evidence")):
        return "Missing evidence prevents review."

    safe_errors = _as_sequence(validation.get("safe_errors"))
    unsafe_codes = {
        ERROR_UNSAFE_FIELD,
        ERROR_UNSAFE_OPERATION,
        ERROR_PERMISSION_DENIED,
    }
    for item in safe_errors:
        if not isinstance(item, Mapping):
            return "Validation safe errors prevent review."
        code = _safe_text(item.get("code")).upper()
        if code in unsafe_codes:
            return "Unsafe or permission-limited validation evidence prevents review."
    if safe_errors:
        return "Validation safe errors prevent review."

    readiness_preview = _as_mapping(validation.get("readiness_preview"))
    readiness_status = _safe_text(readiness_preview.get("status")).upper()
    if readiness_status in {"BLOCKED", "MISSING_EVIDENCE", "PERMISSION_LIMITED"}:
        return "Readiness preview prevents review."
    return None


def _base_response() -> dict[str, Any]:
    return {
        "guardrails": list(NO_LIVE_ACTION_GUARDRAILS),
        "no_live_action_confirmed": True,
    }


def _rejected(
    code: str,
    message: str,
    *,
    current_status: str | None = None,
    idempotency_status: str | None = None,
) -> dict[str, Any]:
    error: dict[str, str] = {"code": code, "message": message}
    if current_status:
        error["current_status"] = current_status
    response = {
        **_base_response(),
        "status": RESULT_REJECTED,
        "error": error,
    }
    if idempotency_status:
        response["idempotency_status"] = idempotency_status
    return response


def _normalise_role(value: Any) -> str:
    return _safe_text(value).upper()


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return value
    return []


def _string_list(value: Any) -> list[str]:
    return [
        str(item).strip() for item in _as_sequence(value) if str(item or "").strip()
    ]
