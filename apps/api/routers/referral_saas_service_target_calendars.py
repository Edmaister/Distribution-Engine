from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.referral_saas_service_target_calendar_service import (
    CALENDAR_GUARDRAILS,
    CALENDAR_REDACTIONS,
    DateException,
    ServiceTargetCalendarConflict,
    ServiceTargetCalendarNotFound,
    ServiceTargetCalendarResolutionUnavailable,
    ServiceTargetCalendarValidationError,
    WeeklyInterval,
    create_service_target_calendar,
    get_service_target_calendar,
    hash_command_value,
    hash_request_payload,
    list_service_target_calendars,
    preview_service_target_calendar,
    resolve_service_target_calendar,
    transition_service_target_calendar,
)
from utils.security import require_session_key


router = APIRouter(
    prefix="/v1/referral-saas/service-target-calendars",
    tags=["Referral SaaS - Service target calendars"],
)
ADMIN_ROLES = {"ADMIN", "SYSTEM_ADMIN", "PLATFORM_ADMIN"}


class WeeklyIntervalRequest(BaseModel):
    localDayOfWeek: int = Field(ge=1, le=7)
    localStartTime: time
    localEndTime: time


class DateExceptionRequest(BaseModel):
    localDate: date
    exceptionType: str = Field(min_length=1)
    localStartTime: time | None = None
    localEndTime: time | None = None
    reasonCode: str = Field(min_length=1)


class CalendarCreateRequest(BaseModel):
    calendarCode: str = Field(min_length=1)
    scopeType: str = Field(min_length=1)
    accountId: str | None = None
    calendarName: str = Field(min_length=1)
    businessTimezone: str = Field(min_length=1)
    effectiveFrom: datetime
    effectiveTo: datetime | None = None
    weeklyIntervals: list[WeeklyIntervalRequest] = Field(default_factory=list)
    dateExceptions: list[DateExceptionRequest] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlationId: str | None = None
    idempotencyKey: str = Field(min_length=1)


class CalendarActionRequest(BaseModel):
    reason: str = Field(min_length=1)
    correlationId: str | None = None
    idempotencyKey: str = Field(min_length=1)


class CalendarPreviewRequest(BaseModel):
    startedAt: datetime
    warningThresholdMinutes: int = Field(ge=0)
    targetDurationMinutes: int = Field(gt=0)


def _admin(identity: dict[str, Any]) -> dict[str, Any]:
    if str(identity.get("role") or "").upper() not in ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "permission_denied",
                "message": "Amplifi administrator access is required.",
            },
        )
    return identity


def _actor(identity: dict[str, Any]) -> str:
    return str(identity.get("subject") or identity.get("client_id") or identity.get("role") or "AMPLIFI_ADMIN")


def _response(calendar: Any, idempotency_status: str | None = None) -> dict[str, Any]:
    body = {
        "status": "ok",
        "calendar": calendar.to_dict(),
        "guardrails": list(CALENDAR_GUARDRAILS),
        "redactions": list(CALENDAR_REDACTIONS),
    }
    if idempotency_status:
        body["idempotencyStatus"] = idempotency_status
    return body


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, ServiceTargetCalendarValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "validation_error", "message": str(exc)},
        )
    if isinstance(exc, ServiceTargetCalendarNotFound):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "calendar_not_found", "message": "Business calendar was not found."},
        )
    if isinstance(exc, ServiceTargetCalendarResolutionUnavailable):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "business_calendar_unavailable", "message": str(exc)},
        )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "calendar_conflict", "message": str(exc)},
    )


@router.post("")
async def create_calendar(request: CalendarCreateRequest, identity: dict = Depends(require_session_key)):
    admin = _admin(identity)
    payload = request.model_dump(mode="json", exclude={"idempotencyKey"})
    try:
        calendar, replay = await create_service_target_calendar(
            calendar_code=request.calendarCode, scope_type=request.scopeType,
            account_id=request.accountId, calendar_name=request.calendarName,
            business_timezone=request.businessTimezone,
            effective_from=request.effectiveFrom, effective_to=request.effectiveTo,
            weekly_intervals=[
                WeeklyInterval(item.localDayOfWeek, item.localStartTime, item.localEndTime)
                for item in request.weeklyIntervals
            ],
            date_exceptions=[
                DateException(
                    item.localDate, item.exceptionType, item.localStartTime,
                    item.localEndTime, item.reasonCode,
                )
                for item in request.dateExceptions
            ],
            metadata=request.metadata, actor_ref=_actor(admin),
            actor_role=str(admin.get("role") or "").upper(),
            correlation_id=request.correlationId or str(uuid.uuid4()),
            idempotency_key_hash=hash_command_value(request.idempotencyKey),
            request_payload_hash=hash_request_payload(payload),
        )
        return _response(calendar, replay)
    except (ServiceTargetCalendarValidationError, ServiceTargetCalendarConflict) as exc:
        raise _translate(exc) from exc


@router.get("")
async def list_calendars(
    lifecycle_status: str | None = Query(default=None, alias="lifecycleStatus"),
    scope_type: str | None = Query(default=None, alias="scopeType"),
    account_id: str | None = Query(default=None, alias="accountId"),
    calendar_code: str | None = Query(default=None, alias="calendarCode"),
    identity: dict = Depends(require_session_key),
):
    _admin(identity)
    try:
        calendars = await list_service_target_calendars(
            lifecycle_status=lifecycle_status, scope_type=scope_type,
            account_id=account_id, calendar_code=calendar_code,
        )
        return {
            "status": "ok", "calendars": [item.to_dict() for item in calendars],
            "count": len(calendars), "guardrails": list(CALENDAR_GUARDRAILS),
            "redactions": list(CALENDAR_REDACTIONS),
        }
    except ServiceTargetCalendarValidationError as exc:
        raise _translate(exc) from exc


@router.get("/resolution")
async def resolve_calendar(
    calendar_code: str = Query(alias="calendarCode"),
    account_id: str | None = Query(default=None, alias="accountId"),
    effective_at: datetime | None = Query(default=None, alias="effectiveAt"),
    identity: dict = Depends(require_session_key),
):
    _admin(identity)
    try:
        calendar = await resolve_service_target_calendar(
            calendar_code=calendar_code, account_id=account_id, effective_at=effective_at,
        )
        return {**_response(calendar), "resolvedAt": effective_at or datetime.now(timezone.utc)}
    except (ServiceTargetCalendarValidationError, ServiceTargetCalendarResolutionUnavailable) as exc:
        raise _translate(exc) from exc


@router.get("/{calendar_ref}")
async def get_calendar(calendar_ref: str, identity: dict = Depends(require_session_key)):
    _admin(identity)
    try:
        return _response(await get_service_target_calendar(calendar_ref))
    except (ServiceTargetCalendarValidationError, ServiceTargetCalendarNotFound) as exc:
        raise _translate(exc) from exc


@router.post("/{calendar_ref}/calculation-preview")
async def preview_calendar(
    calendar_ref: str,
    request: CalendarPreviewRequest,
    identity: dict = Depends(require_session_key),
):
    _admin(identity)
    try:
        preview = await preview_service_target_calendar(
            calendar_ref=calendar_ref,
            started_at=request.startedAt,
            warning_threshold_minutes=request.warningThresholdMinutes,
            target_duration_minutes=request.targetDurationMinutes,
        )
        return {
            "status": "ok",
            "preview": preview,
            "guardrails": [*CALENDAR_GUARDRAILS, "PREVIEW_ONLY_NO_CLOCK_CREATED"],
            "redactions": list(CALENDAR_REDACTIONS),
        }
    except (ServiceTargetCalendarValidationError, ServiceTargetCalendarNotFound) as exc:
        raise _translate(exc) from exc


async def _action(
    calendar_ref: str, action: str, request: CalendarActionRequest, identity: dict,
) -> dict[str, Any]:
    admin = _admin(identity)
    payload = {
        "calendarRef": calendar_ref, "action": action, "reason": request.reason,
        "correlationId": request.correlationId,
    }
    try:
        calendar, replay = await transition_service_target_calendar(
            calendar_ref=calendar_ref, action=action, reason=request.reason,
            actor_ref=_actor(admin), actor_role=str(admin.get("role") or "").upper(),
            correlation_id=request.correlationId or str(uuid.uuid4()),
            idempotency_key_hash=hash_command_value(request.idempotencyKey),
            request_payload_hash=hash_request_payload(payload),
        )
        return _response(calendar, replay)
    except (
        ServiceTargetCalendarValidationError,
        ServiceTargetCalendarNotFound,
        ServiceTargetCalendarConflict,
    ) as exc:
        raise _translate(exc) from exc


@router.post("/{calendar_ref}/submit-review")
async def submit_review(calendar_ref: str, request: CalendarActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(calendar_ref, "SUBMIT_REVIEW", request, identity)


@router.post("/{calendar_ref}/approve")
async def approve(calendar_ref: str, request: CalendarActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(calendar_ref, "APPROVE", request, identity)


@router.post("/{calendar_ref}/return-to-draft")
async def return_to_draft(calendar_ref: str, request: CalendarActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(calendar_ref, "RETURN_TO_DRAFT", request, identity)


@router.post("/{calendar_ref}/retire")
async def retire(calendar_ref: str, request: CalendarActionRequest, identity: dict = Depends(require_session_key)):
    return await _action(calendar_ref, "RETIRE", request, identity)
