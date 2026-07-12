from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from services.onboarding import onboarding_draft_repository as draft_repo
from services.onboarding import onboarding_review_decision_service as review_service
from services.onboarding.onboarding_draft_audit_evidence_service import (
    build_draft_save_audit_evidence,
    build_draft_save_audit_link_fields,
)
from services.onboarding.onboarding_draft_idempotency_service import (
    STATUS_CONFLICT_DIFFERENT_PAYLOAD,
    STATUS_INVALID_IDEMPOTENCY_KEY,
    STATUS_REPLAY_SAME_PAYLOAD,
    evaluate_draft_idempotency,
    hash_payload,
)
from services.onboarding.onboarding_draft_validation_service import (
    ERROR_UNSAFE_FIELD,
    ERROR_UNSAFE_OPERATION,
    validate_onboarding_draft,
)
from services.onboarding.onboarding_readiness_aggregation_service import (
    aggregate_onboarding_readiness,
)
from services.onboarding.onboarding_review_decision_service import (
    RESULT_REJECTED as REVIEW_RESULT_REJECTED,
)
from services.onboarding.onboarding_review_decision_service import (
    RESULT_REPLAYED as REVIEW_RESULT_REPLAYED,
)
from services.onboarding.onboarding_review_decision_service import (
    RESULT_REVIEW_DECISION_RECORDED,
    record_onboarding_draft_review_decision,
)
from services.onboarding.onboarding_state_projection_service import (
    SECTION_DEFINITIONS,
    project_onboarding_state,
)
from services.onboarding.onboarding_submit_for_review_service import (
    ERROR_DRAFT_NOT_FOUND,
    ERROR_IDEMPOTENCY_CONFLICT,
    ERROR_INVALID_STATE,
    ERROR_PERMISSION_DENIED_SUBMIT,
    ERROR_STALE_DRAFT,
    ERROR_VALIDATION_BLOCKED,
    RESULT_REJECTED,
    RESULT_REPLAYED,
    RESULT_SUBMITTED_FOR_REVIEW,
    submit_onboarding_draft_for_review,
)
from services.onboarding.onboarding_submit_for_review_service import (
    NO_LIVE_ACTION_GUARDRAILS as SUBMIT_NO_LIVE_ACTION_GUARDRAILS,
)
from utils.security import require_session_key

router = APIRouter(
    prefix="/admin/onboarding",
    tags=["Admin - Onboarding"],
)

ONBOARDING_ADMIN_ROLES = {
    "ADMIN",
    "SYSTEM_ADMIN",
    "DISTRIBUTION_ADMIN",
    "PLATFORM_ADMIN",
}

NO_LIVE_ACTION_GUARDRAILS = [
    "DRAFT_INTENT_ONLY",
    "NO_LIVE_MUTATION",
    "TENANT_CODE_INTERNAL",
    "NO_SECRET_EXPOSURE",
    "NO_CREDENTIAL_LIFECYCLE",
    "NO_WEBHOOK_DELIVERY",
    "GO_LIVE_DISABLED",
    "NO_MONEY_MOVEMENT",
]


def _require_onboarding_admin(identity: dict[str, Any]) -> dict[str, Any]:
    role = str(identity.get("role") or "").upper()
    if role not in ONBOARDING_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "permission_denied",
                "message": "API key is not authorised for onboarding state.",
            },
        )
    return identity


def _scope(
    *,
    external_tenant_ref: str | None,
    organisation_ref: str | None,
    producer_ref: str | None,
    sponsor_ref: str | None,
    distributor_ref: str | None,
    campaign_code: str | None,
    opportunity_ref: str | None,
) -> dict[str, str]:
    return {
        key: value.strip()
        for key, value in {
            "external_tenant_ref": external_tenant_ref,
            "organisation_ref": organisation_ref,
            "producer_ref": producer_ref,
            "sponsor_ref": sponsor_ref,
            "distributor_ref": distributor_ref,
            "campaign_code": campaign_code,
            "opportunity_ref": opportunity_ref,
        }.items()
        if value is not None and value.strip()
    }


@router.post("/drafts")
async def save_admin_onboarding_draft(
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_onboarding_admin(identity)
    if _contains_user_tenant_code(payload):
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNSAFE_OPERATION_ATTEMPTED",
            message="tenant_code is internal and cannot be supplied as draft scope.",
            details=[_safe_detail("scope", None, "UNSAFE_FIELD")],
            redactions=["internal_identifier"],
        )

    supplied_scope = _scope_from_payload(payload)
    if not supplied_scope.get("external_tenant_ref") or not supplied_scope.get(
        "organisation_ref"
    ):
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message="external_tenant_ref and organisation_ref are required.",
            details=[
                _safe_detail("scope", "external_tenant_ref", "REQUIRED_FIELD_MISSING"),
                _safe_detail("scope", "organisation_ref", "REQUIRED_FIELD_MISSING"),
            ],
        )

    draft_ref = _draft_ref(supplied_scope)
    raw_sections = _raw_sections_from_payload(payload)
    safe_sections = _sections_from_payload(payload)
    validation_payload = {
        "scope": supplied_scope,
        "sections": raw_sections,
    }
    validation = validate_onboarding_draft(
        validation_payload,
        actor_context=_actor_context(admin_identity),
    )
    unsafe_codes = {ERROR_UNSAFE_FIELD, ERROR_UNSAFE_OPERATION}
    if any(item.get("code") in unsafe_codes for item in validation["safe_errors"]):
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNSAFE_OPERATION_ATTEMPTED",
            message="The onboarding draft contains unsafe fields or live actions.",
            details=validation["safe_errors"],
            redactions=validation["redactions"],
        )

    idempotency_key = str(payload.get("idempotency_key") or "").strip()
    request_payload_for_hash = {
        "scope": supplied_scope,
        "sections": safe_sections,
        "correlation_id": _optional_text(payload.get("correlation_id")),
    }
    actor_ref = _actor_ref(admin_identity)
    initial_decision = evaluate_draft_idempotency(
        idempotency_key=idempotency_key,
        actor_ref=actor_ref,
        external_tenant_ref=supplied_scope["external_tenant_ref"],
        operation_type="ONBOARDING_DRAFT_CREATE",
        request_payload=request_payload_for_hash,
        draft_ref=draft_ref,
    )
    if initial_decision.status == STATUS_INVALID_IDEMPOTENCY_KEY:
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message="A valid idempotency key is required.",
            details=[
                _safe_detail(
                    "idempotency",
                    None,
                    str(initial_decision.reason or "INVALID_IDEMPOTENCY_KEY"),
                )
            ],
        )

    existing_idempotency = await draft_repo.get_idempotency_reference(
        idempotency_key_hash=initial_decision.idempotency_key_hash or "",
        scope_hash=initial_decision.scope_hash or "",
    )
    decision = evaluate_draft_idempotency(
        idempotency_key=idempotency_key,
        actor_ref=actor_ref,
        external_tenant_ref=supplied_scope["external_tenant_ref"],
        operation_type="ONBOARDING_DRAFT_CREATE",
        request_payload=request_payload_for_hash,
        existing_reference=existing_idempotency,
        draft_ref=draft_ref,
    )
    if decision.status == STATUS_CONFLICT_DIFFERENT_PAYLOAD:
        raise _safe_http_error(
            status.HTTP_409_CONFLICT,
            code="IDEMPOTENCY_CONFLICT",
            message="The idempotency key was reused with different draft intent.",
            details=[_safe_detail("idempotency", None, "IDEMPOTENCY_CONFLICT")],
        )
    if decision.status == STATUS_REPLAY_SAME_PAYLOAD:
        return _draft_response(
            status_value="replayed",
            draft_ref=draft_ref,
            draft_status=str(existing_idempotency.get("result_status") or "DUPLICATE"),
            idempotency_status=decision.status,
            validation=validation,
        )

    existing_draft = await draft_repo.get_draft_by_ref(draft_ref)
    if existing_draft:
        raise _safe_http_error(
            status.HTTP_409_CONFLICT,
            code="DUPLICATE_DRAFT",
            message="An onboarding draft already exists for this external scope.",
            details=[_safe_detail("draft", "draft_ref", "DUPLICATE_DRAFT")],
        )

    draft = await draft_repo.create_draft(
        draft_ref=draft_ref,
        external_tenant_ref=supplied_scope["external_tenant_ref"],
        organisation_ref=supplied_scope["organisation_ref"],
        producer_ref=supplied_scope.get("producer_ref"),
        sponsor_ref=supplied_scope.get("sponsor_ref"),
        distributor_ref=supplied_scope.get("distributor_ref"),
        campaign_code=supplied_scope.get("campaign_code"),
        opportunity_ref=supplied_scope.get("opportunity_ref"),
        created_by_ref=actor_ref,
        created_by_role=str(admin_identity.get("role") or "ADMIN").upper(),
        correlation_id=_optional_text(payload.get("correlation_id")) or None,
        safe_summary=_safe_summary(validation),
        metadata={"source": "admin_onboarding_draft_save"},
        redactions=validation["redactions"],
    )
    draft_id = str(draft.get("draft_id") or "")
    for section_key, section_payload in safe_sections.items():
        await draft_repo.upsert_draft_section(
            draft_id=draft_id,
            section_key=section_key,
            section_status=_section_status(validation, section_key),
            section_payload=section_payload,
            payload_hash=hash_payload(section_payload),
            redaction_summary={"redactions": validation["redactions"]},
            missing_evidence=[
                item
                for item in validation["missing_evidence"]
                if item.get("section") == section_key
            ],
            source_warnings=[
                item
                for item in validation["warnings"]
                if item.get("section") in {section_key, "readiness"}
            ],
        )

    await draft_repo.record_validation_result(
        draft_id=draft_id,
        draft_version=draft.get("draft_version"),
        validation_scope="ONBOARDING_DRAFT_SAVE",
        validation_status=_validation_status_for_repo(validation),
        validation_type="READINESS",
        safe_error_code=_first_code(validation["safe_errors"]),
        safe_errors=validation["safe_errors"],
        missing_evidence=validation["missing_evidence"],
        blockers=validation["blockers"],
        warnings=validation["warnings"],
        readiness_preview=validation["readiness_preview"],
        details={"no_live_action_confirmed": True},
        correlation_id=_optional_text(payload.get("correlation_id")) or None,
    )

    response = _draft_response(
        status_value="saved",
        draft_ref=draft_ref,
        draft_status=str(draft.get("status") or "DRAFT_CREATED"),
        idempotency_status=decision.status,
        validation=validation,
    )
    idempotency_record = await draft_repo.record_idempotency_reference(
        idempotency_key_hash=decision.idempotency_key_hash or "",
        scope_hash=decision.scope_hash or "",
        actor_ref=actor_ref,
        external_tenant_ref=supplied_scope["external_tenant_ref"],
        operation_type="ONBOARDING_DRAFT_CREATE",
        request_hash=decision.request_hash or "",
        response_hash=hash_payload(
            {
                "status": response["status"],
                "draft_ref": response["draft_ref"],
                "draft_status": response["draft_status"],
            }
        ),
        result_status="SUCCESS",
        draft_id=draft_id,
        draft_ref=draft_ref,
        correlation_id=_optional_text(payload.get("correlation_id")) or None,
    )
    audit_evidence = build_draft_save_audit_evidence(
        actor_ref=actor_ref,
        actor_role=str(admin_identity.get("role") or "ADMIN").upper(),
        permission_scope={
            "route_family": "admin_onboarding",
            "role_family": "admin_operator",
        },
        external_scope=supplied_scope,
        draft_ref=draft_ref,
        draft_version=draft.get("draft_version"),
        action_status="SUCCESS",
        idempotency_reference=decision.idempotency_key_hash,
        correlation_id=_optional_text(payload.get("correlation_id")) or None,
        current_sections=safe_sections,
        validation=validation,
    )
    await draft_repo.create_audit_link_reference(
        **build_draft_save_audit_link_fields(
            draft_id=draft_id,
            evidence=audit_evidence,
            idempotency_id=_optional_text(idempotency_record.get("idempotency_id"))
            or None,
        )
    )
    return response


@router.post("/drafts/{draft_ref}/submit-for-review")
async def submit_admin_onboarding_draft_for_review(
    draft_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_onboarding_admin(identity)
    if _contains_user_tenant_code(payload):
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNSAFE_OPERATION_ATTEMPTED",
            message="tenant_code is internal and cannot be supplied as review scope.",
            details=[_safe_detail("scope", None, "UNSAFE_FIELD")],
            redactions=["internal_identifier"],
        )

    expected_version = _expected_draft_version(payload)
    if expected_version is None:
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message="expected_version is required for submit-for-review.",
            details=[
                _safe_detail("draft", "expected_version", "REQUIRED_FIELD_MISSING")
            ],
        )

    idempotency_key = _optional_text(payload.get("idempotency_key"))
    if not idempotency_key:
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message="A valid idempotency key is required.",
            details=[_safe_detail("idempotency", None, "REQUIRED_FIELD_MISSING")],
        )

    saved_draft = await draft_repo.get_draft_by_ref(draft_ref)
    if not saved_draft:
        raise _submit_http_error(
            status.HTTP_404_NOT_FOUND,
            code=ERROR_DRAFT_NOT_FOUND,
            message="Draft reference is missing or unavailable.",
        )

    supplied_scope = _scope_from_payload(payload)
    if not _draft_matches_scope(saved_draft, supplied_scope):
        raise _submit_http_error(
            status.HTTP_404_NOT_FOUND,
            code=ERROR_DRAFT_NOT_FOUND,
            message="Draft reference is missing or unavailable.",
        )

    section_rows = await draft_repo.get_draft_sections(str(saved_draft["draft_id"]))
    saved_sections = _sections_from_saved_rows(section_rows)
    saved_scope = _scope_from_draft(saved_draft)
    validation = validate_onboarding_draft(
        {
            "scope": saved_scope,
            "sections": saved_sections,
        },
        actor_context=_actor_context(admin_identity),
    )

    result = await submit_onboarding_draft_for_review(
        draft_ref=draft_ref,
        expected_draft_version=expected_version,
        idempotency_key=idempotency_key,
        actor_ref=_actor_ref(admin_identity),
        actor_role=str(admin_identity.get("role") or "ADMIN").upper(),
        validation=validation,
        correlation_id=_optional_text(payload.get("correlation_id")) or None,
    )
    if result["status"] == RESULT_REJECTED:
        code = result["error"]["code"]
        raise _submit_http_error(
            _submit_error_status(code),
            code=code,
            message=result["error"]["message"],
            details=[_safe_detail("draft", None, code)],
            result=result,
            validation=validation,
        )

    return _submit_for_review_response(result=result, validation=validation)


@router.post("/drafts/{draft_ref}/review-decision")
async def record_admin_onboarding_draft_review_decision(
    draft_ref: str,
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_onboarding_admin(identity)
    if _contains_user_tenant_code(payload):
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNSAFE_OPERATION_ATTEMPTED",
            message=(
                "tenant_code is internal and cannot be supplied as review scope."
            ),
            details=[_safe_detail("scope", None, "UNSAFE_FIELD")],
            redactions=["internal_identifier"],
        )

    expected_version = _expected_draft_version(payload)
    if expected_version is None:
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message="expected_version is required for review decision.",
            details=[
                _safe_detail("draft", "expected_version", "REQUIRED_FIELD_MISSING")
            ],
        )

    idempotency_key = _optional_text(payload.get("idempotency_key"))
    if not idempotency_key:
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message="A valid idempotency key is required.",
            details=[_safe_detail("idempotency", None, "REQUIRED_FIELD_MISSING")],
        )

    saved_draft = await draft_repo.get_draft_by_ref(draft_ref)
    if not saved_draft:
        raise _review_http_error(
            status.HTTP_404_NOT_FOUND,
            code=review_service.ERROR_DRAFT_NOT_FOUND,
            message="Draft reference is missing or unavailable.",
        )

    supplied_scope = _scope_from_payload(payload)
    if not _draft_matches_scope(saved_draft, supplied_scope):
        raise _review_http_error(
            status.HTTP_404_NOT_FOUND,
            code=review_service.ERROR_DRAFT_NOT_FOUND,
            message="Draft reference is missing or unavailable.",
        )

    section_rows = await draft_repo.get_draft_sections(str(saved_draft["draft_id"]))
    saved_sections = _sections_from_saved_rows(section_rows)
    validation = validate_onboarding_draft(
        {
            "scope": _scope_from_draft(saved_draft),
            "sections": saved_sections,
        },
        actor_context=_actor_context(admin_identity),
    )

    result = await record_onboarding_draft_review_decision(
        draft_ref=draft_ref,
        expected_draft_version=expected_version,
        idempotency_key=idempotency_key,
        actor_ref=_actor_ref(admin_identity),
        actor_role=str(admin_identity.get("role") or "ADMIN").upper(),
        review_outcome=_optional_text(payload.get("review_outcome")),
        reason_category=_optional_text(payload.get("reason_category")),
        reason=_optional_text(payload.get("reason")),
        validation=validation,
        correlation_id=_optional_text(payload.get("correlation_id")) or None,
    )
    if result["status"] == REVIEW_RESULT_REJECTED:
        code = result["error"]["code"]
        raise _review_http_error(
            _review_error_status(code),
            code=code,
            message=result["error"]["message"],
            details=[_safe_detail("draft", None, code)],
            result=result,
            validation=validation,
        )

    return _review_decision_response(result=result, validation=validation)


@router.post("/validate")
async def validate_admin_onboarding_dry_run(
    payload: dict[str, Any] = Body(default_factory=dict),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    admin_identity = _require_onboarding_admin(identity)
    if _contains_user_tenant_code(payload):
        raise _safe_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="UNSAFE_OPERATION_ATTEMPTED",
            message=(
                "tenant_code is internal and cannot be supplied as validation scope."
            ),
            details=[_safe_detail("scope", None, "UNSAFE_FIELD")],
            redactions=["internal_identifier"],
        )

    supplied_scope = _scope_from_payload(payload)
    raw_sections = _raw_sections_from_payload(payload)
    validation = validate_onboarding_draft(
        {
            "scope": supplied_scope,
            "sections": raw_sections,
        },
        actor_context=_actor_context(admin_identity),
    )
    guardrails = sorted(
        set(validation["guardrails"]).union(
            {
                "NO_AUDIT_WRITE",
                "NO_EVENT_PERSISTENCE",
                "NO_EVENT_DISPATCH",
            }
        )
    )
    return {
        "status": validation["status"],
        "validation_result": validation["validation_result"],
        "readiness_preview": validation["readiness_preview"],
        "missing_evidence": validation["missing_evidence"],
        "blockers": validation["blockers"],
        "warnings": validation["warnings"],
        "safe_errors": validation["safe_errors"],
        "next_actions": validation["next_actions"],
        "guardrails": guardrails,
        "redactions": validation["redactions"],
        "no_persistence_confirmed": True,
        "no_live_action_confirmed": True,
    }


@router.get("/state")
async def get_admin_onboarding_state(
    external_tenant_ref: str | None = Query(default=None),
    organisation_ref: str | None = Query(default=None),
    producer_ref: str | None = Query(default=None),
    sponsor_ref: str | None = Query(default=None),
    distributor_ref: str | None = Query(default=None),
    campaign_code: str | None = Query(default=None),
    opportunity_ref: str | None = Query(default=None),
    identity: dict = Depends(require_session_key),
) -> dict[str, Any]:
    _require_onboarding_admin(identity)
    supplied_scope = _scope(
        external_tenant_ref=external_tenant_ref,
        organisation_ref=organisation_ref,
        producer_ref=producer_ref,
        sponsor_ref=sponsor_ref,
        distributor_ref=distributor_ref,
        campaign_code=campaign_code,
        opportunity_ref=opportunity_ref,
    )
    projection = project_onboarding_state({"scope": supplied_scope})
    readiness = aggregate_onboarding_readiness(projection)

    return {
        "status": "ok",
        "onboarding_state": projection,
        "readiness": readiness,
        "guardrail": (
            "Read-only admin onboarding state. This endpoint uses supplied "
            "external references and explicit shell-only or missing-evidence "
            "markers. It does not create or update onboarding records, create "
            "accounts, send invitations, publish campaigns, create credentials, "
            "deliver webhooks, fund, fulfil, settle, retry, mutate audit, "
            "activate go-live, or move money."
        ),
    }


def _scope_from_payload(payload: Mapping[str, Any]) -> dict[str, str]:
    body_scope = payload.get("scope")
    scope_source = body_scope if isinstance(body_scope, Mapping) else payload
    return {
        key: value
        for key, value in _scope(
            external_tenant_ref=_maybe_text(scope_source.get("external_tenant_ref")),
            organisation_ref=_maybe_text(scope_source.get("organisation_ref")),
            producer_ref=_maybe_text(scope_source.get("producer_ref")),
            sponsor_ref=_maybe_text(scope_source.get("sponsor_ref")),
            distributor_ref=_maybe_text(scope_source.get("distributor_ref")),
            campaign_code=_maybe_text(scope_source.get("campaign_code")),
            opportunity_ref=_maybe_text(scope_source.get("opportunity_ref")),
        ).items()
        if value
    }


def _sections_from_payload(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    section_source = payload.get("draft_sections") or payload.get("sections") or {}
    if not isinstance(section_source, Mapping):
        return {}
    sections: dict[str, dict[str, Any]] = {}
    for section_key, definition in SECTION_DEFINITIONS.items():
        source = section_source.get(section_key)
        if not isinstance(source, Mapping):
            continue
        sections[section_key] = {
            field: source.get(field)
            for field in definition["fields"]
            if source.get(field) is not None
        }
    return sections


def _raw_sections_from_payload(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    section_source = payload.get("draft_sections") or payload.get("sections") or {}
    if not isinstance(section_source, Mapping):
        return {}
    return {
        section_key: dict(source)
        for section_key, source in section_source.items()
        if section_key in SECTION_DEFINITIONS and isinstance(source, Mapping)
    }


def _contains_user_tenant_code(payload: Mapping[str, Any]) -> bool:
    if "tenant_code" in payload:
        return True
    scope = payload.get("scope")
    return isinstance(scope, Mapping) and "tenant_code" in scope


def _expected_draft_version(payload: Mapping[str, Any]) -> int | None:
    raw_value = payload.get("expected_version", payload.get("expected_draft_version"))
    if isinstance(raw_value, bool):
        return None
    if isinstance(raw_value, int) and raw_value > 0:
        return raw_value
    if isinstance(raw_value, str) and raw_value.strip().isdigit():
        value = int(raw_value.strip())
        return value if value > 0 else None
    return None


def _scope_from_draft(draft: Mapping[str, Any]) -> dict[str, str]:
    return {
        key: value
        for key, value in _scope(
            external_tenant_ref=_maybe_text(draft.get("external_tenant_ref")),
            organisation_ref=_maybe_text(draft.get("organisation_ref")),
            producer_ref=_maybe_text(draft.get("producer_ref")),
            sponsor_ref=_maybe_text(draft.get("sponsor_ref")),
            distributor_ref=_maybe_text(draft.get("distributor_ref")),
            campaign_code=_maybe_text(draft.get("campaign_code")),
            opportunity_ref=_maybe_text(draft.get("opportunity_ref")),
        ).items()
        if value
    }


def _draft_matches_scope(
    draft: Mapping[str, Any],
    supplied_scope: Mapping[str, str],
) -> bool:
    saved_scope = _scope_from_draft(draft)
    return all(saved_scope.get(key) == value for key, value in supplied_scope.items())


def _sections_from_saved_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    sections: dict[str, dict[str, Any]] = {}
    for row in rows:
        section_key = _optional_text(row.get("section_key"))
        if section_key not in SECTION_DEFINITIONS:
            continue
        payload = row.get("section_payload")
        if isinstance(payload, Mapping):
            sections[section_key] = dict(payload)
    return sections


def _draft_ref(scope: Mapping[str, str]) -> str:
    digest = hash_payload({key: scope.get(key) for key in sorted(scope)})
    return f"draft_{digest[:20]}"


def _actor_ref(identity: Mapping[str, Any]) -> str:
    return (
        _optional_text(identity.get("subject"))
        or _optional_text(identity.get("client_id"))
        or _optional_text(identity.get("role"))
        or "ONBOARDING_ADMIN"
    )


def _actor_context(identity: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "actor_ref": _actor_ref(identity),
        "actor_role": str(identity.get("role") or "").upper(),
    }


def _safe_summary(validation: Mapping[str, Any]) -> dict[str, Any]:
    readiness = validation.get("readiness_preview") or {}
    return {
        "validation_status": validation["validation_result"]["status"],
        "readiness_status": readiness.get("overall_status"),
        "missing_evidence_count": len(validation["missing_evidence"]),
        "blocker_count": len(validation["blockers"]),
        "redactions": validation["redactions"],
        "no_live_action_confirmed": True,
    }


def _section_status(validation: Mapping[str, Any], section_key: str) -> str:
    if any(item.get("section") == section_key for item in validation["blockers"]):
        return "BLOCKED"
    if any(
        item.get("section") == section_key for item in validation["missing_evidence"]
    ):
        return "IN_PROGRESS"
    return "READY"


def _validation_status_for_repo(validation: Mapping[str, Any]) -> str:
    status_value = str(validation["validation_result"]["status"] or "").upper()
    if status_value in {"VALID"}:
        return "PASSED"
    if status_value in {"MISSING_EVIDENCE"}:
        return "WARNING"
    if status_value in {"BLOCKED", "PERMISSION_LIMITED"}:
        return "BLOCKED"
    return "FAILED"


def _first_code(items: list[dict[str, Any]]) -> str | None:
    return str(items[0].get("code")) if items else None


def _draft_response(
    *,
    status_value: str,
    draft_ref: str,
    draft_status: str,
    idempotency_status: str,
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": status_value,
        "draft_ref": draft_ref,
        "draft_status": draft_status,
        "idempotency_status": idempotency_status,
        "validation_result": validation["validation_result"],
        "validation_summary": {
            "status": validation["validation_result"]["status"],
            "safe_error_count": len(validation["safe_errors"]),
            "missing_evidence_count": len(validation["missing_evidence"]),
            "blocker_count": len(validation["blockers"]),
        },
        "readiness_preview": validation["readiness_preview"],
        "missing_evidence": validation["missing_evidence"],
        "blockers": validation["blockers"],
        "next_actions": validation["next_actions"],
        "guardrails": sorted(
            set(NO_LIVE_ACTION_GUARDRAILS).union(validation["guardrails"])
        ),
        "redactions": validation["redactions"],
        "no_live_action_confirmed": True,
    }


def _submit_for_review_response(
    *,
    result: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": _submit_status_value(str(result["status"])),
        "draft_ref": result.get("draft_ref"),
        "draft_status": result.get("draft_status"),
        "draft_version": result.get("draft_version"),
        "idempotency_status": result.get("idempotency_status"),
        "validation_result": validation["validation_result"],
        "validation_summary": {
            "status": validation["validation_result"]["status"],
            "safe_error_count": len(validation["safe_errors"]),
            "missing_evidence_count": len(validation["missing_evidence"]),
            "blocker_count": len(validation["blockers"]),
        },
        "readiness_summary": _submit_readiness_summary(validation),
        "missing_evidence": validation["missing_evidence"],
        "blockers": validation["blockers"],
        "next_actions": _submit_next_actions(validation.get("next_actions")),
        "guardrails": _submit_guardrails(
            result["guardrails"], validation["guardrails"]
        ),
        "redactions": _submit_redactions(validation.get("redactions")),
        "audit_evidence_ref": result.get("audit_evidence_ref"),
        "audit_link_ref": result.get("audit_link_ref"),
        "audit_evidence_status": result.get("audit_evidence_status") or "NOT_RECORDED",
        "no_live_action_confirmed": True,
    }


def _review_decision_response(
    *,
    result: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "status": _review_status_value(str(result["status"])),
        "draft_ref": result.get("draft_ref"),
        "previous_status": result.get("previous_status"),
        "draft_status": result.get("draft_status"),
        "draft_version": result.get("draft_version"),
        "review_outcome": result.get("review_outcome"),
        "reason_category": result.get("reason_category"),
        "idempotency_status": result.get("idempotency_status"),
        "validation_result": validation["validation_result"],
        "validation_summary": {
            "status": validation["validation_result"]["status"],
            "safe_error_count": len(validation["safe_errors"]),
            "missing_evidence_count": len(validation["missing_evidence"]),
            "blocker_count": len(validation["blockers"]),
        },
        "readiness_summary": _submit_readiness_summary(validation),
        "missing_evidence": validation["missing_evidence"],
        "blockers": validation["blockers"],
        "next_actions": _submit_next_actions(validation.get("next_actions")),
        "guardrails": _submit_guardrails(
            result["guardrails"], validation["guardrails"]
        ),
        "redactions": _submit_redactions(validation.get("redactions")),
        "audit_evidence_ref": None,
        "audit_link_ref": None,
        "audit_evidence_status": "NOT_RECORDED_IN_TASK_124",
        "approval_to_launch": False,
        "go_live_enabled": False,
        "no_live_action_confirmed": True,
    }


def _review_status_value(result_status: str) -> str:
    if result_status == RESULT_REVIEW_DECISION_RECORDED:
        return "review_decision_recorded"
    if result_status == REVIEW_RESULT_REPLAYED:
        return "replayed"
    return result_status.lower()


def _submit_status_value(result_status: str) -> str:
    if result_status == RESULT_SUBMITTED_FOR_REVIEW:
        return "submitted_for_review"
    if result_status == RESULT_REPLAYED:
        return "replayed"
    return result_status.lower()


def _submit_readiness_summary(validation: Mapping[str, Any]) -> dict[str, Any]:
    readiness = _as_mapping(validation.get("readiness_preview"))
    summary = _as_mapping(readiness.get("summary"))
    return {
        "overall_status": _optional_text(readiness.get("overall_status")),
        "ready_count": summary.get("ready_count", 0),
        "blocked_count": summary.get("blocked_count", 0),
        "missing_evidence_count": summary.get("missing_evidence_count", 0),
        "go_live_disabled_count": summary.get("go_live_disabled_count", 0),
        "total_count": summary.get("total_count", 0),
        "go_live_enabled": False,
    }


def _submit_error_status(code: str) -> int:
    if code == ERROR_DRAFT_NOT_FOUND:
        return status.HTTP_404_NOT_FOUND
    if code in {ERROR_IDEMPOTENCY_CONFLICT, ERROR_INVALID_STATE, ERROR_STALE_DRAFT}:
        return status.HTTP_409_CONFLICT
    if code in {
        ERROR_VALIDATION_BLOCKED,
        ERROR_PERMISSION_DENIED_SUBMIT,
    }:
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    return status.HTTP_422_UNPROCESSABLE_ENTITY


def _review_error_status(code: str) -> int:
    if code == review_service.ERROR_DRAFT_NOT_FOUND:
        return status.HTTP_404_NOT_FOUND
    if code in {
        review_service.ERROR_IDEMPOTENCY_CONFLICT,
        review_service.ERROR_INVALID_STATE,
        review_service.ERROR_STALE_DRAFT,
    }:
        return status.HTTP_409_CONFLICT
    return status.HTTP_422_UNPROCESSABLE_ENTITY


def _review_http_error(
    http_status: int,
    *,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    result: Mapping[str, Any] | None = None,
    validation: Mapping[str, Any] | None = None,
) -> HTTPException:
    detail: dict[str, Any] = {
        "code": code,
        "message": message,
        "details": details or [_safe_detail("draft", None, code)],
        "guardrails": _submit_guardrails(
            _as_list(
                _as_mapping(result).get("guardrails")
                if isinstance(result, Mapping)
                else []
            ),
            review_service.NO_LIVE_ACTION_GUARDRAILS,
        ),
        "audit_evidence_ref": None,
        "audit_link_ref": None,
        "audit_evidence_status": "NOT_RECORDED_IN_TASK_124",
        "approval_to_launch": False,
        "go_live_enabled": False,
        "no_live_action_confirmed": True,
    }
    if isinstance(result, Mapping) and result.get("idempotency_status"):
        detail["idempotency_status"] = result["idempotency_status"]
    if isinstance(result, Mapping) and result.get("review_outcome"):
        detail["review_outcome"] = result["review_outcome"]
    if isinstance(validation, Mapping):
        detail["validation_summary"] = {
            "status": _as_mapping(validation.get("validation_result")).get("status"),
            "safe_error_count": len(_as_list(validation.get("safe_errors"))),
            "missing_evidence_count": len(_as_list(validation.get("missing_evidence"))),
            "blocker_count": len(_as_list(validation.get("blockers"))),
        }
        detail["blockers"] = _as_list(validation.get("blockers"))
        detail["next_actions"] = _submit_next_actions(validation.get("next_actions"))
        detail["redactions"] = _submit_redactions(validation.get("redactions"))
    return HTTPException(status_code=http_status, detail=detail)


def _submit_http_error(
    http_status: int,
    *,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    result: Mapping[str, Any] | None = None,
    validation: Mapping[str, Any] | None = None,
) -> HTTPException:
    detail: dict[str, Any] = {
        "code": code,
        "message": message,
        "details": details or [_safe_detail("draft", None, code)],
        "guardrails": _submit_guardrails(
            _as_list(
                _as_mapping(result).get("guardrails")
                if isinstance(result, Mapping)
                else []
            ),
            SUBMIT_NO_LIVE_ACTION_GUARDRAILS,
        ),
        "audit_evidence_ref": None,
        "audit_link_ref": None,
        "audit_evidence_status": "NOT_RECORDED_IN_TASK_116",
        "no_live_action_confirmed": True,
    }
    if isinstance(result, Mapping) and result.get("idempotency_status"):
        detail["idempotency_status"] = result["idempotency_status"]
    if isinstance(validation, Mapping):
        detail["validation_summary"] = {
            "status": _as_mapping(validation.get("validation_result")).get("status"),
            "safe_error_count": len(_as_list(validation.get("safe_errors"))),
            "missing_evidence_count": len(_as_list(validation.get("missing_evidence"))),
            "blocker_count": len(_as_list(validation.get("blockers"))),
        }
        detail["blockers"] = _as_list(validation.get("blockers"))
        detail["next_actions"] = _submit_next_actions(validation.get("next_actions"))
        detail["redactions"] = _submit_redactions(validation.get("redactions"))
    return HTTPException(status_code=http_status, detail=detail)


def _submit_guardrails(*sources: Any) -> list[str]:
    guardrails: set[str] = set()
    replacements = {
        "NO_MONEY_MOVEMENT": "NO_VALUE_TRANSFER",
        "NO_SECRET_EXPOSURE": "NO_SENSITIVE_MATERIAL_EXPOSURE",
        "TENANT_CODE_INTERNAL": "INTERNAL_TENANT_IDENTIFIER_ONLY",
        "NO_WEBHOOK_DELIVERY": "NO_WEBHOOK_DISPATCH",
    }
    for source in sources:
        for item in _as_list(source):
            text = _optional_text(item)
            if not text:
                continue
            guardrails.add(replacements.get(text, text))
    return sorted(guardrails)


def _submit_next_actions(source: Any) -> list[str]:
    actions: list[str] = []
    for action in _as_list(source):
        text = str(action)
        text = text.replace("tenant_code", "internal tenant identifier")
        text = text.replace("approved read-only", "verified read-only")
        actions.append(text)
    return actions


def _submit_redactions(source: Any) -> list[str]:
    redactions: list[str] = []
    replacements = {
        "money_movement_internal": "value_transfer_internal",
    }
    for item in _as_list(source):
        text = str(item)
        redactions.append(replacements.get(text, text))
    return redactions


def _safe_http_error(
    http_status: int,
    *,
    code: str,
    message: str,
    details: list[dict[str, Any]],
    redactions: list[str] | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail={
            "code": code,
            "message": message,
            "details": details,
            "redactions": redactions or [],
            "no_live_action_confirmed": True,
        },
    )


def _safe_detail(
    section: str,
    field: str | None,
    code: str,
) -> dict[str, str | None]:
    return {
        "section": section,
        "field": field,
        "code": code,
        "message": "The onboarding draft request could not be saved safely.",
    }


def _maybe_text(value: Any) -> str | None:
    text = _optional_text(value)
    return text or None


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _optional_text(value: Any) -> str:
    return str(value or "").strip()
