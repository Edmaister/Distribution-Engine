"""Governed administration and resolution for service-target business calendars."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timezone
from hashlib import sha256
from typing import Any, Mapping, Sequence

from services.referral_saas_service_target_business_calendar import (
    BusinessCalendarValidationError,
    BusinessCalendarVersion as CalculationCalendarVersion,
    LocalWorkingInterval,
)
from utils.db import db_connection


CALENDAR_GUARDRAILS = (
    "AMPLIFI_ADMIN_GOVERNED",
    "INDEPENDENT_APPROVAL_REQUIRED",
    "APPROVED_EFFECTIVE_VERSION_ONLY",
    "ACCOUNT_SCOPE_PREFERRED_OVER_GLOBAL",
    "FAIL_CLOSED_ON_MISSING_OR_AMBIGUOUS_CALENDAR",
    "NO_CLOCK_MUTATION",
    "NO_CAMPAIGN_OR_MONEY_SIDE_EFFECTS",
)
CALENDAR_REDACTIONS = (
    "idempotency_key_hash",
    "request_payload_hash",
    "internal_tenant_identifier",
    "provider_secret",
)
CALENDAR_LIFECYCLE_STATUSES = {"DRAFT", "IN_REVIEW", "APPROVED", "RETIRED"}


class ServiceTargetCalendarError(Exception):
    """Base calendar-governance error."""


class ServiceTargetCalendarValidationError(ServiceTargetCalendarError):
    pass


class ServiceTargetCalendarNotFound(ServiceTargetCalendarError):
    pass


class ServiceTargetCalendarConflict(ServiceTargetCalendarError):
    pass


class ServiceTargetCalendarResolutionUnavailable(ServiceTargetCalendarError):
    pass


@dataclass(frozen=True)
class WeeklyInterval:
    local_day_of_week: int
    local_start_time: time
    local_end_time: time


@dataclass(frozen=True)
class DateException:
    local_date: date
    exception_type: str
    local_start_time: time | None
    local_end_time: time | None
    reason_code: str


@dataclass(frozen=True)
class ServiceTargetCalendarVersion:
    calendar_version_id: str
    calendar_code: str
    version_number: int
    scope_type: str
    account_id: str | None
    calendar_name: str
    business_timezone: str
    lifecycle_status: str
    effective_from: datetime
    effective_to: datetime | None
    created_by_ref: str
    reviewed_by_ref: str | None
    reviewed_at: datetime | None
    approved_by_ref: str | None
    approved_at: datetime | None
    metadata: Mapping[str, Any]
    created_at: datetime
    updated_at: datetime
    retired_at: datetime | None
    weekly_intervals: tuple[WeeklyInterval, ...]
    date_exceptions: tuple[DateException, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def hash_command_value(value: str) -> str:
    return sha256(value.strip().encode("utf-8")).hexdigest()


def hash_request_payload(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _row_value(row: Mapping[str, Any], key: str, default: Any = None) -> Any:
    try:
        return row[key]
    except (KeyError, TypeError):
        return default


def _json_value(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return value


def _normalise_code(value: str, field: str) -> str:
    normalised = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    if not normalised or len(normalised) > 120:
        raise ServiceTargetCalendarValidationError(f"{field} must contain 1 to 120 characters.")
    if not all(character.isalnum() or character == "_" for character in normalised):
        raise ServiceTargetCalendarValidationError(
            f"{field} must contain only letters, numbers, or underscores."
        )
    return normalised


def _normalise_datetime(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ServiceTargetCalendarValidationError(f"{field} must include a timezone offset.")
    return value.astimezone(timezone.utc)


def _calendar_from_rows(
    row: Mapping[str, Any],
    weekly_rows: Sequence[Mapping[str, Any]],
    exception_rows: Sequence[Mapping[str, Any]],
) -> ServiceTargetCalendarVersion:
    return ServiceTargetCalendarVersion(
        calendar_version_id=str(_row_value(row, "service_target_calendar_version_id")),
        calendar_code=str(_row_value(row, "calendar_code")),
        version_number=int(_row_value(row, "version_number")),
        scope_type=str(_row_value(row, "scope_type")),
        account_id=str(_row_value(row, "account_id")) if _row_value(row, "account_id") else None,
        calendar_name=str(_row_value(row, "calendar_name")),
        business_timezone=str(_row_value(row, "business_timezone")),
        lifecycle_status=str(_row_value(row, "lifecycle_status")),
        effective_from=_row_value(row, "effective_from"),
        effective_to=_row_value(row, "effective_to"),
        created_by_ref=str(_row_value(row, "created_by_ref")),
        reviewed_by_ref=_row_value(row, "reviewed_by_ref"),
        reviewed_at=_row_value(row, "reviewed_at"),
        approved_by_ref=_row_value(row, "approved_by_ref"),
        approved_at=_row_value(row, "approved_at"),
        metadata=_json_value(_row_value(row, "metadata"), {}),
        created_at=_row_value(row, "created_at"),
        updated_at=_row_value(row, "updated_at"),
        retired_at=_row_value(row, "retired_at"),
        weekly_intervals=tuple(
            WeeklyInterval(
                local_day_of_week=int(_row_value(item, "local_day_of_week")),
                local_start_time=_row_value(item, "local_start_time"),
                local_end_time=_row_value(item, "local_end_time"),
            )
            for item in weekly_rows
        ),
        date_exceptions=tuple(
            DateException(
                local_date=_row_value(item, "local_date"),
                exception_type=str(_row_value(item, "exception_type")),
                local_start_time=_row_value(item, "local_start_time"),
                local_end_time=_row_value(item, "local_end_time"),
                reason_code=str(_row_value(item, "reason_code")),
            )
            for item in exception_rows
        ),
    )


def _validate_schedule(
    *,
    calendar_code: str,
    version_number: int,
    business_timezone: str,
    weekly_intervals: Sequence[WeeklyInterval],
    date_exceptions: Sequence[DateException],
) -> None:
    weekly: dict[int, list[LocalWorkingInterval]] = {}
    closed_dates: set[date] = set()
    exceptional: dict[date, list[LocalWorkingInterval]] = {}
    for interval in weekly_intervals:
        weekly.setdefault(interval.local_day_of_week, []).append(
            LocalWorkingInterval(interval.local_start_time, interval.local_end_time)
        )
    for exception in date_exceptions:
        kind = _normalise_code(exception.exception_type, "exceptionType")
        _normalise_code(exception.reason_code, "reasonCode")
        if kind == "CLOSED":
            if exception.local_start_time is not None or exception.local_end_time is not None:
                raise ServiceTargetCalendarValidationError("Closed dates cannot include working times.")
            closed_dates.add(exception.local_date)
        elif kind == "WORKING_INTERVAL":
            if exception.local_start_time is None or exception.local_end_time is None:
                raise ServiceTargetCalendarValidationError(
                    "Exceptional working intervals require start and end times."
                )
            exceptional.setdefault(exception.local_date, []).append(
                LocalWorkingInterval(exception.local_start_time, exception.local_end_time)
            )
        else:
            raise ServiceTargetCalendarValidationError("exceptionType is invalid.")
    try:
        CalculationCalendarVersion(
            calendar_code=calendar_code,
            version_number=version_number,
            business_timezone=business_timezone,
            lifecycle_status="APPROVED",
            weekly_intervals={key: tuple(value) for key, value in weekly.items()},
            closed_dates=frozenset(closed_dates),
            exceptional_working_intervals={key: tuple(value) for key, value in exceptional.items()},
        )
    except BusinessCalendarValidationError as exc:
        raise ServiceTargetCalendarValidationError(str(exc)) from exc


async def _load_calendar(conn: Any, calendar_ref: str, *, for_update: bool = False) -> ServiceTargetCalendarVersion:
    try:
        calendar_id = uuid.UUID(calendar_ref)
    except ValueError as exc:
        raise ServiceTargetCalendarValidationError("calendarRef must be a UUID.") from exc
    suffix = " FOR UPDATE" if for_update else ""
    row = await conn.fetchrow(
        "SELECT * FROM referral_saas_service_target_calendar_versions "
        "WHERE service_target_calendar_version_id = $1" + suffix,
        calendar_id,
    )
    if not row:
        raise ServiceTargetCalendarNotFound(calendar_ref)
    weekly = await conn.fetch(
        "SELECT * FROM referral_saas_service_target_calendar_weekly_intervals "
        "WHERE service_target_calendar_version_id = $1 "
        "ORDER BY local_day_of_week, local_start_time",
        calendar_id,
    )
    exceptions = await conn.fetch(
        "SELECT * FROM referral_saas_service_target_calendar_date_exceptions "
        "WHERE service_target_calendar_version_id = $1 "
        "ORDER BY local_date, exception_type, local_start_time NULLS FIRST",
        calendar_id,
    )
    return _calendar_from_rows(row, weekly, exceptions)


async def _audit(
    conn: Any,
    *,
    calendar: ServiceTargetCalendarVersion,
    event_type: str,
    event_status: str,
    actor_ref: str,
    actor_role: str,
    reason_code: str,
    correlation_id: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
    evidence_summary: Mapping[str, Any],
) -> None:
    await conn.execute(
        """
        INSERT INTO referral_saas_service_target_calendar_audit (
            service_target_calendar_audit_id, service_target_calendar_version_id,
            account_id, event_type, event_status, actor_ref, actor_role, reason_code,
            correlation_id, idempotency_key_hash, request_payload_hash,
            evidence_summary, redactions
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13::jsonb)
        """,
        uuid.uuid4(), uuid.UUID(calendar.calendar_version_id),
        uuid.UUID(calendar.account_id) if calendar.account_id else None,
        event_type, event_status, actor_ref, actor_role, reason_code,
        correlation_id, idempotency_key_hash, request_payload_hash,
        json.dumps(dict(evidence_summary)), json.dumps(list(CALENDAR_REDACTIONS)),
    )


async def create_service_target_calendar(
    *,
    calendar_code: str,
    scope_type: str,
    account_id: str | None,
    calendar_name: str,
    business_timezone: str,
    effective_from: datetime,
    effective_to: datetime | None,
    weekly_intervals: Sequence[WeeklyInterval],
    date_exceptions: Sequence[DateException],
    metadata: Mapping[str, Any],
    actor_ref: str,
    actor_role: str,
    correlation_id: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
) -> tuple[ServiceTargetCalendarVersion, str]:
    code = _normalise_code(calendar_code, "calendarCode")
    scope = _normalise_code(scope_type, "scopeType")
    if scope not in {"GLOBAL", "ACCOUNT"}:
        raise ServiceTargetCalendarValidationError("scopeType must be GLOBAL or ACCOUNT.")
    if scope == "GLOBAL" and account_id:
        raise ServiceTargetCalendarValidationError("Global calendars cannot include accountId.")
    if scope == "ACCOUNT" and not account_id:
        raise ServiceTargetCalendarValidationError("Account calendars require accountId.")
    try:
        safe_account_id = uuid.UUID(account_id) if account_id else None
    except ValueError as exc:
        raise ServiceTargetCalendarValidationError("accountId must be a UUID.") from exc
    name = str(calendar_name or "").strip()
    if not name or len(name) > 200:
        raise ServiceTargetCalendarValidationError("calendarName must contain 1 to 200 characters.")
    start = _normalise_datetime(effective_from, "effectiveFrom")
    end = _normalise_datetime(effective_to, "effectiveTo") if effective_to else None
    if end and end <= start:
        raise ServiceTargetCalendarValidationError("effectiveTo must be later than effectiveFrom.")

    async with db_connection() as conn:
        async with conn.transaction():
            replay = await conn.fetchrow(
                "SELECT service_target_calendar_version_id, request_payload_hash "
                "FROM referral_saas_service_target_calendar_versions WHERE idempotency_key_hash = $1",
                idempotency_key_hash,
            )
            if replay:
                if _row_value(replay, "request_payload_hash") != request_payload_hash:
                    raise ServiceTargetCalendarConflict(
                        "Idempotency key was reused with different calendar content."
                    )
                return await _load_calendar(
                    conn, str(_row_value(replay, "service_target_calendar_version_id"))
                ), "REPLAY_SAME_PAYLOAD"
            version_number = await conn.fetchval(
                """
                SELECT COALESCE(MAX(version_number), 0) + 1
                FROM referral_saas_service_target_calendar_versions
                WHERE UPPER(calendar_code) = $1 AND scope_type = $2
                  AND account_id IS NOT DISTINCT FROM $3
                """,
                code, scope, safe_account_id,
            )
            _validate_schedule(
                calendar_code=code, version_number=version_number,
                business_timezone=business_timezone, weekly_intervals=weekly_intervals,
                date_exceptions=date_exceptions,
            )
            calendar_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO referral_saas_service_target_calendar_versions (
                    service_target_calendar_version_id, calendar_code, version_number,
                    scope_type, account_id, calendar_name, business_timezone,
                    lifecycle_status, effective_from, effective_to, created_by_ref,
                    correlation_id, idempotency_key_hash, request_payload_hash,
                    metadata, redactions
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'DRAFT', $8, $9, $10,
                          $11, $12, $13, $14::jsonb, $15::jsonb)
                """,
                calendar_id, code, version_number, scope, safe_account_id, name,
                business_timezone, start, end, actor_ref, correlation_id,
                idempotency_key_hash, request_payload_hash, json.dumps(dict(metadata)),
                json.dumps(list(CALENDAR_REDACTIONS)),
            )
            for interval in weekly_intervals:
                await conn.execute(
                    """
                    INSERT INTO referral_saas_service_target_calendar_weekly_intervals (
                        service_target_calendar_weekly_interval_id,
                        service_target_calendar_version_id, local_day_of_week,
                        local_start_time, local_end_time
                    ) VALUES ($1, $2, $3, $4, $5)
                    """,
                    uuid.uuid4(), calendar_id, interval.local_day_of_week,
                    interval.local_start_time, interval.local_end_time,
                )
            for exception in date_exceptions:
                await conn.execute(
                    """
                    INSERT INTO referral_saas_service_target_calendar_date_exceptions (
                        service_target_calendar_date_exception_id,
                        service_target_calendar_version_id, local_date, exception_type,
                        local_start_time, local_end_time, reason_code
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    uuid.uuid4(), calendar_id, exception.local_date,
                    _normalise_code(exception.exception_type, "exceptionType"),
                    exception.local_start_time, exception.local_end_time,
                    _normalise_code(exception.reason_code, "reasonCode"),
                )
            calendar = await _load_calendar(conn, str(calendar_id))
            await _audit(
                conn, calendar=calendar, event_type="CALENDAR_CREATED",
                event_status="RECORDED", actor_ref=actor_ref, actor_role=actor_role,
                reason_code="NEW_CALENDAR_VERSION", correlation_id=correlation_id,
                idempotency_key_hash=idempotency_key_hash,
                request_payload_hash=request_payload_hash,
                evidence_summary={
                    "calendarCode": code, "versionNumber": version_number,
                    "scopeType": scope, "weeklyIntervalCount": len(weekly_intervals),
                    "dateExceptionCount": len(date_exceptions), "nextStatus": "DRAFT",
                },
            )
            return calendar, "NEW_REQUEST"


async def get_service_target_calendar(calendar_ref: str) -> ServiceTargetCalendarVersion:
    async with db_connection() as conn:
        return await _load_calendar(conn, calendar_ref)


async def list_service_target_calendars(
    *, lifecycle_status: str | None = None, scope_type: str | None = None,
    account_id: str | None = None, calendar_code: str | None = None,
) -> list[ServiceTargetCalendarVersion]:
    status = _normalise_code(lifecycle_status, "lifecycleStatus") if lifecycle_status else None
    if status and status not in CALENDAR_LIFECYCLE_STATUSES:
        raise ServiceTargetCalendarValidationError("lifecycleStatus is invalid.")
    scope = _normalise_code(scope_type, "scopeType") if scope_type else None
    if scope and scope not in {"GLOBAL", "ACCOUNT"}:
        raise ServiceTargetCalendarValidationError("scopeType is invalid.")
    try:
        safe_account_id = uuid.UUID(account_id) if account_id else None
    except ValueError as exc:
        raise ServiceTargetCalendarValidationError("accountId must be a UUID.") from exc
    code = _normalise_code(calendar_code, "calendarCode") if calendar_code else None
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT service_target_calendar_version_id
            FROM referral_saas_service_target_calendar_versions
            WHERE ($1::text IS NULL OR lifecycle_status = $1)
              AND ($2::text IS NULL OR scope_type = $2)
              AND ($3::uuid IS NULL OR account_id = $3)
              AND ($4::text IS NULL OR UPPER(calendar_code) = $4)
            ORDER BY calendar_code, scope_type, account_id NULLS FIRST, version_number DESC
            """,
            status, scope, safe_account_id, code,
        )
        return [
            await _load_calendar(conn, str(_row_value(row, "service_target_calendar_version_id")))
            for row in rows
        ]


async def transition_service_target_calendar(
    *, calendar_ref: str, action: str, reason: str, actor_ref: str, actor_role: str,
    correlation_id: str, idempotency_key_hash: str, request_payload_hash: str,
) -> tuple[ServiceTargetCalendarVersion, str]:
    safe_action = _normalise_code(action, "action")
    transitions = {
        "SUBMIT_REVIEW": ("DRAFT", "IN_REVIEW"),
        "APPROVE": ("IN_REVIEW", "APPROVED"),
        "RETURN_TO_DRAFT": ("IN_REVIEW", "DRAFT"),
        "RETIRE": ("APPROVED", "RETIRED"),
    }
    if safe_action not in transitions:
        raise ServiceTargetCalendarValidationError("Unsupported calendar lifecycle action.")
    reason_code = str(reason or "").strip()
    if not reason_code:
        raise ServiceTargetCalendarValidationError("reason is required.")
    expected, next_status = transitions[safe_action]
    async with db_connection() as conn:
        async with conn.transaction():
            calendar = await _load_calendar(conn, calendar_ref, for_update=True)
            replay = await conn.fetchrow(
                """
                SELECT request_payload_hash
                FROM referral_saas_service_target_calendar_audit
                WHERE service_target_calendar_version_id = $1
                  AND event_type = $2 AND idempotency_key_hash = $3
                ORDER BY created_at DESC LIMIT 1
                """,
                uuid.UUID(calendar_ref), f"CALENDAR_{safe_action}", idempotency_key_hash,
            )
            if replay:
                if _row_value(replay, "request_payload_hash") != request_payload_hash:
                    raise ServiceTargetCalendarConflict(
                        "Idempotency key was reused with different lifecycle content."
                    )
                return calendar, "REPLAY_SAME_PAYLOAD"
            if calendar.lifecycle_status != expected:
                raise ServiceTargetCalendarConflict(
                    f"{safe_action} requires {expected}; current status is {calendar.lifecycle_status}."
                )
            if safe_action in {"APPROVE", "RETURN_TO_DRAFT"} and actor_ref == calendar.created_by_ref:
                raise ServiceTargetCalendarConflict(
                    "Calendar review must be performed by an actor other than the creator."
                )
            if safe_action == "APPROVE":
                _validate_schedule(
                    calendar_code=calendar.calendar_code,
                    version_number=calendar.version_number,
                    business_timezone=calendar.business_timezone,
                    weekly_intervals=calendar.weekly_intervals,
                    date_exceptions=calendar.date_exceptions,
                )
                overlap = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM referral_saas_service_target_calendar_versions
                        WHERE service_target_calendar_version_id <> $1
                          AND UPPER(calendar_code) = $2
                          AND scope_type = $3
                          AND account_id IS NOT DISTINCT FROM $4
                          AND lifecycle_status = 'APPROVED'
                          AND effective_from < COALESCE($6, 'infinity'::timestamptz)
                          AND COALESCE(effective_to, 'infinity'::timestamptz) > $5
                    )
                    """,
                    uuid.UUID(calendar_ref), calendar.calendar_code, calendar.scope_type,
                    uuid.UUID(calendar.account_id) if calendar.account_id else None,
                    calendar.effective_from, calendar.effective_to,
                )
                if overlap:
                    raise ServiceTargetCalendarConflict(
                        "An approved calendar already covers this scope and effective window."
                    )
            await conn.execute(
                """
                UPDATE referral_saas_service_target_calendar_versions
                SET lifecycle_status = $2,
                    reviewed_by_ref = CASE WHEN $3 IN ('APPROVE', 'RETURN_TO_DRAFT') THEN $4 ELSE reviewed_by_ref END,
                    reviewed_at = CASE WHEN $3 IN ('APPROVE', 'RETURN_TO_DRAFT') THEN NOW() ELSE reviewed_at END,
                    approved_by_ref = CASE WHEN $3 = 'APPROVE' THEN $4 ELSE approved_by_ref END,
                    approved_at = CASE WHEN $3 = 'APPROVE' THEN NOW() ELSE approved_at END,
                    retired_at = CASE WHEN $3 = 'RETIRE' THEN NOW() ELSE retired_at END,
                    updated_at = NOW()
                WHERE service_target_calendar_version_id = $1
                """,
                uuid.UUID(calendar_ref), next_status, safe_action, actor_ref,
            )
            updated = await _load_calendar(conn, calendar_ref)
            await _audit(
                conn, calendar=updated, event_type=f"CALENDAR_{safe_action}",
                event_status="RECORDED", actor_ref=actor_ref, actor_role=actor_role,
                reason_code=reason_code, correlation_id=correlation_id,
                idempotency_key_hash=idempotency_key_hash,
                request_payload_hash=request_payload_hash,
                evidence_summary={
                    "previousStatus": calendar.lifecycle_status,
                    "nextStatus": next_status,
                    "calendarCode": calendar.calendar_code,
                    "versionNumber": calendar.version_number,
                },
            )
            return updated, "NEW_REQUEST"


async def resolve_service_target_calendar(
    *, calendar_code: str, effective_at: datetime | None = None,
    account_id: str | None = None,
) -> ServiceTargetCalendarVersion:
    code = _normalise_code(calendar_code, "calendarCode")
    at = _normalise_datetime(effective_at, "effectiveAt") if effective_at else datetime.now(timezone.utc)
    try:
        safe_account_id = uuid.UUID(account_id) if account_id else None
    except ValueError as exc:
        raise ServiceTargetCalendarValidationError("accountId must be a UUID.") from exc
    async with db_connection() as conn:
        if safe_account_id:
            account_rows = await conn.fetch(
                """
                SELECT service_target_calendar_version_id
                FROM referral_saas_service_target_calendar_versions
                WHERE UPPER(calendar_code) = $1 AND scope_type = 'ACCOUNT'
                  AND account_id = $2 AND lifecycle_status = 'APPROVED'
                  AND effective_from <= $3 AND (effective_to IS NULL OR effective_to > $3)
                ORDER BY version_number DESC LIMIT 2
                """,
                code, safe_account_id, at,
            )
            rows = account_rows
        else:
            rows = []
        if not rows:
            rows = await conn.fetch(
                """
                SELECT service_target_calendar_version_id
                FROM referral_saas_service_target_calendar_versions
                WHERE UPPER(calendar_code) = $1 AND scope_type = 'GLOBAL'
                  AND account_id IS NULL AND lifecycle_status = 'APPROVED'
                  AND effective_from <= $2 AND (effective_to IS NULL OR effective_to > $2)
                ORDER BY version_number DESC LIMIT 2
                """,
                code, at,
            )
        if not rows:
            raise ServiceTargetCalendarResolutionUnavailable(
                "No approved effective business calendar covers this scope."
            )
        if len(rows) > 1:
            raise ServiceTargetCalendarResolutionUnavailable(
                "Multiple approved business calendars cover this scope."
            )
        calendar = await _load_calendar(
            conn, str(_row_value(rows[0], "service_target_calendar_version_id"))
        )
    _validate_schedule(
        calendar_code=calendar.calendar_code, version_number=calendar.version_number,
        business_timezone=calendar.business_timezone,
        weekly_intervals=calendar.weekly_intervals,
        date_exceptions=calendar.date_exceptions,
    )
    return calendar
