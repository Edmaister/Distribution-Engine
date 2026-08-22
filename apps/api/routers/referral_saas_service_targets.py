from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.referral_saas_operational_service_target_service import (
    POLICY_GUARDRAILS,
    POLICY_REDACTIONS,
    ServiceTargetPolicyConflict,
    ServiceTargetPolicyNotFound,
    ServiceTargetPolicyResolutionUnavailable,
    ServiceTargetPolicyValidationError,
    create_service_target_policy,
    hash_command_value,
    hash_request_payload,
    list_service_target_policies,
    resolve_service_target_policy,
    transition_service_target_policy,
)
from utils.security import require_session_key


router = APIRouter(prefix="/v1/referral-saas/service-target-policies", tags=["Referral SaaS - Service targets"])
ADMIN_ROLES = {"ADMIN", "SYSTEM_ADMIN", "PLATFORM_ADMIN"}


class PolicyCreateRequest(BaseModel):
    policyCode: str = Field(min_length=1)
    operatingJurisdictionCode: str = Field(min_length=1)
    workType: str = Field(min_length=1)
    workCategory: str = Field(min_length=1)
    priority: str = Field(min_length=1)
    businessTimezone: str = Field(min_length=1)
    targetDurationMinutes: int = Field(gt=0)
    warningThresholdMinutes: int = Field(ge=0)
    businessCalendarRef: str | None = None
    startEvent: str = Field(min_length=1)
    completionEvent: str = Field(min_length=1)
    approvedPauseReasons: list[str] = Field(default_factory=list)
    effectiveFrom: datetime
    effectiveTo: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlationId: str | None = None
    idempotencyKey: str = Field(min_length=1)


class PolicyActionRequest(BaseModel):
    reason: str = Field(min_length=1)
    correlationId: str | None = None
    idempotencyKey: str = Field(min_length=1)


def _admin(identity: dict[str, Any]) -> dict[str, Any]:
    if str(identity.get("role") or "").upper() not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail={"code": "permission_denied", "message": "Amplifi administrator access is required."})
    return identity


def _actor(identity: dict[str, Any]) -> str:
    return str(identity.get("subject") or identity.get("client_id") or identity.get("role") or "AMPLIFI_ADMIN")


def _response(policy: Any, idempotency_status: str | None = None) -> dict[str, Any]:
    body = {"status": "ok", "policy": policy.to_dict(), "guardrails": list(POLICY_GUARDRAILS), "redactions": list(POLICY_REDACTIONS)}
    if idempotency_status:
        body["idempotencyStatus"] = idempotency_status
    return body


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, ServiceTargetPolicyValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail={"code": "validation_error", "message": str(exc)})
    if isinstance(exc, ServiceTargetPolicyNotFound):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "policy_not_found", "message": "Service-target policy was not found."})
    if isinstance(exc, ServiceTargetPolicyResolutionUnavailable):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "service_target_policy_unavailable", "message": str(exc)})
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "policy_conflict", "message": str(exc)})


@router.post("")
async def create_policy(request: PolicyCreateRequest, identity: dict = Depends(require_session_key)):
    admin = _admin(identity)
    payload = request.model_dump(mode="json", exclude={"idempotencyKey"})
    try:
        policy, replay = await create_service_target_policy(
            policy_code=request.policyCode, operating_jurisdiction_code=request.operatingJurisdictionCode,
            work_type=request.workType, work_category=request.workCategory, priority=request.priority,
            business_timezone=request.businessTimezone, target_duration_minutes=request.targetDurationMinutes,
            warning_threshold_minutes=request.warningThresholdMinutes, business_calendar_ref=request.businessCalendarRef,
            start_event=request.startEvent, completion_event=request.completionEvent,
            approved_pause_reasons=request.approvedPauseReasons, effective_from=request.effectiveFrom,
            effective_to=request.effectiveTo, metadata=request.metadata, actor_ref=_actor(admin),
            actor_role=str(admin.get("role") or "").upper(), correlation_id=request.correlationId or str(uuid.uuid4()),
            idempotency_key_hash=hash_command_value(request.idempotencyKey), request_payload_hash=hash_request_payload(payload),
        )
        return _response(policy, replay)
    except (ServiceTargetPolicyValidationError, ServiceTargetPolicyConflict) as exc:
        raise _translate(exc) from exc


@router.get("")
async def list_policies(
    lifecycle_status: str | None = Query(default=None, alias="lifecycleStatus"),
    operating_jurisdiction_code: str | None = Query(default=None, alias="operatingJurisdictionCode"),
    work_type: str | None = Query(default=None, alias="workType"),
    work_category: str | None = Query(default=None, alias="workCategory"),
    priority: str | None = None,
    identity: dict = Depends(require_session_key),
):
    _admin(identity)
    try:
        policies = await list_service_target_policies(
            lifecycle_status=lifecycle_status, operating_jurisdiction_code=operating_jurisdiction_code,
            work_type=work_type, work_category=work_category, priority=priority,
        )
        return {"status": "ok", "policies": [item.to_dict() for item in policies], "count": len(policies), "guardrails": list(POLICY_GUARDRAILS), "redactions": list(POLICY_REDACTIONS)}
    except ServiceTargetPolicyValidationError as exc:
        raise _translate(exc) from exc


@router.get("/resolution")
async def resolve_policy(
    operating_jurisdiction_code: str = Query(alias="operatingJurisdictionCode"),
    work_type: str = Query(alias="workType"), work_category: str = Query(alias="workCategory"),
    priority: str = Query(), effective_at: datetime | None = Query(default=None, alias="effectiveAt"),
    identity: dict = Depends(require_session_key),
):
    _admin(identity)
    try:
        policy = await resolve_service_target_policy(
            operating_jurisdiction_code=operating_jurisdiction_code, work_type=work_type,
            work_category=work_category, priority=priority, effective_at=effective_at,
        )
        return {**_response(policy), "resolvedAt": effective_at or datetime.now(timezone.utc)}
    except (ServiceTargetPolicyValidationError, ServiceTargetPolicyResolutionUnavailable) as exc:
        raise _translate(exc) from exc


async def _action(policy_ref: str, action: str, request: PolicyActionRequest, identity: dict) -> dict[str, Any]:
    admin = _admin(identity)
    payload = {"policyRef": policy_ref, "action": action, "reason": request.reason, "correlationId": request.correlationId}
    try:
        policy, replay = await transition_service_target_policy(
            policy_ref=policy_ref, action=action, reason=request.reason, actor_ref=_actor(admin),
            actor_role=str(admin.get("role") or "").upper(), correlation_id=request.correlationId or str(uuid.uuid4()),
            idempotency_key_hash=hash_command_value(request.idempotencyKey), request_payload_hash=hash_request_payload(payload),
        )
        return _response(policy, replay)
    except (ServiceTargetPolicyValidationError, ServiceTargetPolicyNotFound, ServiceTargetPolicyConflict) as exc:
        raise _translate(exc) from exc


@router.post("/{policy_ref}/submit-review")
async def submit_review(policy_ref: str, request: PolicyActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(policy_ref, "SUBMIT_REVIEW", request, identity)


@router.post("/{policy_ref}/approve")
async def approve(policy_ref: str, request: PolicyActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(policy_ref, "APPROVE", request, identity)


@router.post("/{policy_ref}/return-to-draft")
async def return_to_draft(policy_ref: str, request: PolicyActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(policy_ref, "RETURN_TO_DRAFT", request, identity)


@router.post("/{policy_ref}/retire")
async def retire(policy_ref: str, request: PolicyActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(policy_ref, "RETIRE", request, identity)
