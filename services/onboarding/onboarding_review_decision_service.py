from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from services.onboarding import onboarding_draft_repository as draft_repo
from services.onboarding.onboarding_draft_audit_evidence_service import (
    build_review_decision_audit_evidence,
    build_review_decision_audit_link_fields,
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

OPERATION_REVIEW_DECISION: Final = "ONBOARDING_DRAFT_REVIEW_DECISION"

SOURCE_READY_FOR_REVIEW: Final = "READY_FOR_REVIEW"
TARGET_BLOCKED: Final = "BLOCKED"

OUTCOME_APPROVED_FOR_INTERNAL_REVIEW: Final = "APPROVED_FOR_INTERNAL_REVIEW"
OUTCOME_BLOCKED: Final = "BLOCKED"
OUTCOME_CHANGES_REQUESTED: Final = "CHANGES_REQUESTED"
OUTCOME_REJECTED: Final = "REJECTED"

SUPPORTED_REVIEW_OUTCOMES: Final = frozenset(
    {
        OUTCOME_APPROVED_FOR_INTERNAL_REVIEW,
        OUTCOME_BLOCKED,
    }
)
UNSUPPORTED_SCHEMA_OUTCOMES: Final = frozenset(
    {
        OUTCOME_CHANGES_REQUESTED,
        OUTCOME_REJECTED,
    }
)

RESULT_REVIEW_DECISION_RECORDED: Final = "REVIEW_DECISION_RECORDED"
RESULT_REPLAYED: Final = "REPLAYED"
RESULT_REJECTED: Final = "REJECTED"

ERROR_DRAFT_NOT_FOUND: Final = "DRAFT_NOT_FOUND"
ERROR_INVALID_STATE: Final = "INVALID_STATE"
ERROR_STALE_DRAFT: Final = "STALE_DRAFT"
ERROR_IDEMPOTENCY_CONFLICT: Final = "IDEMPOTENCY_CONFLICT"
ERROR_VALIDATION_BLOCKED: Final = "VALIDATION_BLOCKED"
ERROR_PERMISSION_DENIED_REVIEW: Final = "PERMISSION_DENIED"
ERROR_UNSUPPORTED_REVIEW_OUTCOME: Final = "UNSUPPORTED_REVIEW_OUTCOME"
ERROR_UNSUPPORTED_SCHEMA_STATE: Final = "UNSUPPORTED_SCHEMA_STATE"
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
    "REVIEW_DECISION_ONLY",
    "NO_LIVE_MUTATION",
    "INTERNAL_TENANT_IDENTIFIER_ONLY",
    "NO_SECRET_EXPOSURE",
    "NO_APPROVAL_TO_LAUNCH",
    "NO_ACCOUNT_CREATION",
    "NO_INVITE_DELIVERY",
    "NO_CAMPAIGN_PUBLICATION",
    "NO_CREDENTIAL_LIFECYCLE",
    "NO_WEBHOOK_DISPATCH",
    "NO_AUDIT_EVENT_DISPATCH",
    "GO_LIVE_DISABLED",
    "NO_MONEY_MOVEMENT",
]


def target_status_for_review_outcome(review_outcome: str) -> str | None:
    outcome = _normalise_outcome(review_outcome)
    if outcome == OUTCOME_APPROVED_FOR_INTERNAL_REVIEW:
        return SOURCE_READY_FOR_REVIEW
    if outcome == OUTCOME_BLOCKED:
        return TARGET_BLOCKED
    return None


def build_review_decision_request_payload(
    *,
    draft_ref: str,
    expected_draft_version: int,
    review_outcome: str,
    reason_category: str,
    reason: str,
    validation: Mapping[str, Any],
    target_status: str | None = None,
) -> dict[str, Any]:
    outcome = _normalise_outcome(review_outcome)
    validation_result = _as_mapping(validation.get("validation_result"))
    return {
        "draft_ref": _safe_text(draft_ref),
        "expected_draft_version": expected_draft_version,
        "operation_type": OPERATION_REVIEW_DECISION,
        "review_outcome": outcome,
        "reason_category": _normalise_outcome(reason_category),
        "reason_hash": hash_payload({"reason": _safe_text(reason)}),
        "target_status": target_status or target_status_for_review_outcome(outcome),
        "validation_status": _safe_text(validation_result.get("status")),
    }


async def record_onboarding_draft_review_decision(
    *,
    draft_ref: str,
    expected_draft_version: int,
    idempotency_key: str,
    actor_ref: str,
    actor_role: str,
    review_outcome: str,
    reason_category: str,
    reason: str,
    validation: Mapping[str, Any],
    correlation_id: str | None = None,
) -> dict[str, Any]:
    role = _normalise_role(actor_role)
    if role not in ONBOARDING_ADMIN_ROLES:
        return _rejected(
            ERROR_PERMISSION_DENIED_REVIEW,
            "Actor is not authorised to record onboarding review decisions.",
        )

    outcome = _normalise_outcome(review_outcome)
    if outcome in UNSUPPORTED_SCHEMA_OUTCOMES:
        return _rejected(
            ERROR_UNSUPPORTED_SCHEMA_STATE,
            "Review outcome requires reviewed schema support before persistence.",
            review_outcome=outcome,
        )
    if outcome not in SUPPORTED_REVIEW_OUTCOMES:
        return _rejected(
            ERROR_UNSUPPORTED_REVIEW_OUTCOME,
            "Review outcome is not supported by the current review contract.",
            review_outcome=outcome or None,
        )

    reason_text = _safe_text(reason)
    if not reason_text:
        return _rejected(
            ERROR_VALIDATION_BLOCKED,
            "A review decision reason is required.",
            review_outcome=outcome,
        )

    target_status = target_status_for_review_outcome(outcome)
    if target_status is None:
        return _rejected(
            ERROR_UNSUPPORTED_SCHEMA_STATE,
            "Review outcome has no schema-backed target state.",
            review_outcome=outcome,
        )

    draft = await draft_repo.get_draft_by_ref(draft_ref)
    if not draft:
        return _rejected(
            ERROR_DRAFT_NOT_FOUND,
            "Draft reference is missing or unavailable.",
            review_outcome=outcome,
        )

    external_tenant_ref = _safe_text(draft.get("external_tenant_ref"))
    if not external_tenant_ref:
        return _rejected(
            ERROR_VALIDATION_BLOCKED,
            "Draft external scope is unavailable.",
            review_outcome=outcome,
        )

    request_payload = build_review_decision_request_payload(
        draft_ref=draft_ref,
        expected_draft_version=expected_draft_version,
        review_outcome=outcome,
        reason_category=reason_category,
        reason=reason_text,
        validation=validation,
        target_status=target_status,
    )
    initial_decision = evaluate_draft_idempotency(
        idempotency_key=idempotency_key,
        actor_ref=actor_ref,
        external_tenant_ref=external_tenant_ref,
        operation_type=OPERATION_REVIEW_DECISION,
        draft_ref=draft_ref,
        request_payload=request_payload,
    )
    if initial_decision.status == STATUS_INVALID_IDEMPOTENCY_KEY:
        return _rejected(
            ERROR_VALIDATION_BLOCKED,
            "A valid idempotency key is required for review decision.",
            review_outcome=outcome,
        )

    existing_reference = await draft_repo.get_idempotency_reference(
        idempotency_key_hash=initial_decision.idempotency_key_hash or "",
        scope_hash=initial_decision.scope_hash or "",
    )
    decision = evaluate_draft_idempotency(
        idempotency_key=idempotency_key,
        actor_ref=actor_ref,
        external_tenant_ref=external_tenant_ref,
        operation_type=OPERATION_REVIEW_DECISION,
        draft_ref=draft_ref,
        request_payload=request_payload,
        existing_reference=existing_reference,
    )

    if decision.status == STATUS_REPLAY_SAME_PAYLOAD:
        return {
            **_base_response(),
            "status": RESULT_REPLAYED,
            "draft_ref": _safe_text(draft_ref),
            "draft_status": target_status,
            "review_outcome": outcome,
            "idempotency_status": decision.status,
        }
    if decision.status == STATUS_CONFLICT_DIFFERENT_PAYLOAD:
        return _rejected(
            ERROR_IDEMPOTENCY_CONFLICT,
            "Idempotency key was reused with a different review-decision payload.",
            idempotency_status=decision.status,
            review_outcome=outcome,
        )

    current_status = _safe_text(draft.get("status")).upper()
    if current_status != SOURCE_READY_FOR_REVIEW:
        return _rejected(
            ERROR_INVALID_STATE,
            "Draft cannot receive a review decision from its current state.",
            current_status=current_status or None,
            review_outcome=outcome,
        )

    validation_blocker = _validation_blocker(validation)
    if validation_blocker:
        return _rejected(
            ERROR_VALIDATION_BLOCKED,
            validation_blocker,
            review_outcome=outcome,
        )

    reason_hash = hash_payload({"reason": reason_text})
    try:
        updated = await draft_repo.update_draft_metadata_or_status(
            draft_ref=draft_ref,
            expected_draft_version=expected_draft_version,
            status=target_status,
            metadata={
                "review_decision": {
                    "operation_type": OPERATION_REVIEW_DECISION,
                    "review_outcome": outcome,
                    "reason_category": _normalise_outcome(reason_category),
                    "reason_hash": reason_hash,
                    "target_status": target_status,
                    "no_live_action_confirmed": True,
                }
            },
            safe_summary={
                "review_decision": {
                    "previous_status": current_status,
                    "target_status": target_status,
                    "review_outcome": outcome,
                    "no_live_action_confirmed": True,
                    "approval_to_launch": False,
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
            review_outcome=outcome,
        )

    response = {
        **_base_response(),
        "status": RESULT_REVIEW_DECISION_RECORDED,
        "draft_ref": _safe_text(draft_ref),
        "previous_status": current_status,
        "draft_status": _safe_text(updated.get("status")) or target_status,
        "draft_version": updated.get("draft_version"),
        "review_outcome": outcome,
        "reason_category": _normalise_outcome(reason_category),
        "idempotency_status": decision.status,
        "approval_to_launch": False,
        "go_live_enabled": False,
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
    audit_evidence = build_review_decision_audit_evidence(
        actor_ref=actor_ref,
        actor_role=role,
        permission_scope={
            "route_family": "admin_onboarding",
            "role_family": "admin_operator",
        },
        prior_draft=draft,
        updated_draft=updated,
        action_status="SUCCESS",
        review_outcome=outcome,
        reason_category=reason_category,
        reason_reference=reason_hash,
        idempotency_reference=decision.idempotency_key_hash,
        correlation_id=correlation_id,
        validation=validation,
        target_status=target_status,
    )
    audit_link = await draft_repo.create_audit_link_reference(
        **build_review_decision_audit_link_fields(
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
        return "Current validation evidence does not allow review decision."
    if _as_sequence(validation.get("blockers")):
        return "Validation blockers prevent review decision."
    if _as_sequence(validation.get("missing_evidence")):
        return "Missing evidence prevents review decision."

    safe_errors = _as_sequence(validation.get("safe_errors"))
    unsafe_codes = {
        ERROR_UNSAFE_FIELD,
        ERROR_UNSAFE_OPERATION,
        ERROR_PERMISSION_DENIED,
    }
    for item in safe_errors:
        if not isinstance(item, Mapping):
            return "Validation safe errors prevent review decision."
        code = _safe_text(item.get("code")).upper()
        if code in unsafe_codes:
            return "Unsafe or permission-limited validation evidence prevents review decision."
    if safe_errors:
        return "Validation safe errors prevent review decision."

    readiness_preview = _as_mapping(validation.get("readiness_preview"))
    readiness_status = _safe_text(readiness_preview.get("status")).upper()
    if readiness_status in {"BLOCKED", "MISSING_EVIDENCE", "PERMISSION_LIMITED"}:
        return "Readiness preview prevents review decision."
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
    review_outcome: str | None = None,
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
    if review_outcome:
        response["review_outcome"] = review_outcome
    return response


def _normalise_role(value: Any) -> str:
    return _safe_text(value).upper()


def _normalise_outcome(value: Any) -> str:
    return _safe_text(value).upper().replace("-", "_").replace(" ", "_")


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
