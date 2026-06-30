from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from services.onboarding import onboarding_draft_repository as draft_repo
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
from services.onboarding.onboarding_state_projection_service import (
    SECTION_DEFINITIONS,
    project_onboarding_state,
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


def _optional_text(value: Any) -> str:
    return str(value or "").strip()
