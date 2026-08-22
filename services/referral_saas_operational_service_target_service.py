"""Governed Referral SaaS operational service-target policy lifecycle."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from utils.db import db_connection


POLICY_GUARDRAILS = (
    "AMPLIFI_ADMIN_GOVERNED",
    "APPROVED_EFFECTIVE_VERSION_ONLY",
    "FAIL_CLOSED_ON_MISSING_OR_AMBIGUOUS_POLICY",
    "NO_CLOCK_MUTATION",
    "NO_CUSTOMER_OR_TENANT_OVERRIDE",
    "NO_BILLING_OR_MONEY_MOVEMENT",
)
POLICY_REDACTIONS = (
    "idempotency_key_hash",
    "request_payload_hash",
    "internal_tenant_identifier",
)
POLICY_LIFECYCLE_STATUSES = {"DRAFT", "IN_REVIEW", "APPROVED", "RETIRED"}


class ServiceTargetPolicyError(Exception):
    """Base policy error."""


class ServiceTargetPolicyValidationError(ServiceTargetPolicyError):
    pass


class ServiceTargetPolicyNotFound(ServiceTargetPolicyError):
    pass


class ServiceTargetPolicyConflict(ServiceTargetPolicyError):
    pass


class ServiceTargetPolicyResolutionUnavailable(ServiceTargetPolicyError):
    pass


@dataclass(frozen=True)
class ServiceTargetPolicy:
    policy_id: str
    policy_code: str
    version_number: int
    operating_jurisdiction_code: str
    work_type: str
    work_category: str
    priority: str
    business_timezone: str
    target_duration_minutes: int
    warning_threshold_minutes: int
    business_calendar_ref: str | None
    start_event: str
    completion_event: str
    approved_pause_reasons: tuple[str, ...]
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

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["approved_pause_reasons"] = list(self.approved_pause_reasons)
        return value


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


def _policy_from_row(row: Mapping[str, Any]) -> ServiceTargetPolicy:
    return ServiceTargetPolicy(
        policy_id=str(_row_value(row, "service_target_policy_id")),
        policy_code=str(_row_value(row, "policy_code")),
        version_number=int(_row_value(row, "version_number")),
        operating_jurisdiction_code=str(_row_value(row, "operating_jurisdiction_code")),
        work_type=str(_row_value(row, "work_type")),
        work_category=str(_row_value(row, "work_category")),
        priority=str(_row_value(row, "priority")),
        business_timezone=str(_row_value(row, "business_timezone")),
        target_duration_minutes=int(_row_value(row, "target_duration_minutes")),
        warning_threshold_minutes=int(_row_value(row, "warning_threshold_minutes")),
        business_calendar_ref=_row_value(row, "business_calendar_ref"),
        start_event=str(_row_value(row, "start_event")),
        completion_event=str(_row_value(row, "completion_event")),
        approved_pause_reasons=tuple(_json_value(_row_value(row, "approved_pause_reasons"), [])),
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
    )


def _normalise_code(value: str, field: str) -> str:
    normalised = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    if not normalised or len(normalised) > 120:
        raise ServiceTargetPolicyValidationError(f"{field} must contain 1 to 120 characters.")
    if not all(char.isalnum() or char == "_" for char in normalised):
        raise ServiceTargetPolicyValidationError(f"{field} must contain only letters, numbers, or underscores.")
    return normalised


def _normalise_datetime(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ServiceTargetPolicyValidationError(f"{field} must include a timezone offset.")
    return value.astimezone(timezone.utc)


def _validate_policy_values(
    *,
    business_timezone: str,
    target_duration_minutes: int,
    warning_threshold_minutes: int,
    effective_from: datetime,
    effective_to: datetime | None,
    approved_pause_reasons: list[str],
) -> tuple[datetime, datetime | None, tuple[str, ...]]:
    start = _normalise_datetime(effective_from, "effectiveFrom")
    end = _normalise_datetime(effective_to, "effectiveTo") if effective_to else None
    try:
        ZoneInfo(business_timezone)
    except ZoneInfoNotFoundError as exc:
        raise ServiceTargetPolicyValidationError("businessTimezone must be a valid IANA timezone.") from exc
    if target_duration_minutes <= 0:
        raise ServiceTargetPolicyValidationError("targetDurationMinutes must be greater than zero.")
    if warning_threshold_minutes < 0 or warning_threshold_minutes >= target_duration_minutes:
        raise ServiceTargetPolicyValidationError(
            "warningThresholdMinutes must be non-negative and less than targetDurationMinutes."
        )
    if end and end <= start:
        raise ServiceTargetPolicyValidationError("effectiveTo must be later than effectiveFrom.")
    pause_reasons = tuple(dict.fromkeys(_normalise_code(item, "approvedPauseReasons") for item in approved_pause_reasons))
    return start, end, pause_reasons


async def _audit(
    conn: Any,
    *,
    policy_id: str,
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
        INSERT INTO referral_saas_operational_service_target_audit (
            service_target_audit_id, entity_type, entity_ref, event_type,
            event_status, actor_ref, actor_role, reason_code, correlation_id,
            idempotency_key_hash, request_payload_hash, evidence_summary, redactions
        ) VALUES ($1, 'POLICY', $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb, $12::jsonb)
        """,
        uuid.uuid4(), uuid.UUID(policy_id), event_type, event_status, actor_ref,
        actor_role, reason_code, correlation_id, idempotency_key_hash,
        request_payload_hash, json.dumps(dict(evidence_summary)), json.dumps(list(POLICY_REDACTIONS)),
    )


async def create_service_target_policy(
    *,
    policy_code: str,
    operating_jurisdiction_code: str,
    work_type: str,
    work_category: str,
    priority: str,
    business_timezone: str,
    target_duration_minutes: int,
    warning_threshold_minutes: int,
    start_event: str,
    completion_event: str,
    effective_from: datetime,
    effective_to: datetime | None,
    approved_pause_reasons: list[str],
    business_calendar_ref: str | None,
    metadata: Mapping[str, Any],
    actor_ref: str,
    actor_role: str,
    correlation_id: str,
    idempotency_key_hash: str,
    request_payload_hash: str,
) -> tuple[ServiceTargetPolicy, str]:
    code = _normalise_code(policy_code, "policyCode")
    jurisdiction = _normalise_code(operating_jurisdiction_code, "operatingJurisdictionCode")
    safe_work_type = _normalise_code(work_type, "workType")
    category = _normalise_code(work_category, "workCategory")
    safe_priority = _normalise_code(priority, "priority")
    safe_start_event = _normalise_code(start_event, "startEvent")
    safe_completion_event = _normalise_code(completion_event, "completionEvent")
    start, end, pause_reasons = _validate_policy_values(
        business_timezone=business_timezone,
        target_duration_minutes=target_duration_minutes,
        warning_threshold_minutes=warning_threshold_minutes,
        effective_from=effective_from,
        effective_to=effective_to,
        approved_pause_reasons=approved_pause_reasons,
    )
    async with db_connection() as conn:
        async with conn.transaction():
            replay = await conn.fetchrow(
                "SELECT * FROM referral_saas_operational_service_target_policies WHERE idempotency_key_hash = $1",
                idempotency_key_hash,
            )
            if replay:
                if _row_value(replay, "request_payload_hash") != request_payload_hash:
                    raise ServiceTargetPolicyConflict("Idempotency key was reused with different policy content.")
                return _policy_from_row(replay), "REPLAY_SAME_PAYLOAD"
            version_number = await conn.fetchval(
                "SELECT COALESCE(MAX(version_number), 0) + 1 FROM referral_saas_operational_service_target_policies WHERE policy_code = $1",
                code,
            )
            policy_id = uuid.uuid4()
            row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_operational_service_target_policies (
                    service_target_policy_id, policy_code, version_number,
                    operating_jurisdiction_code, work_type, work_category, priority,
                    business_timezone, target_duration_minutes, warning_threshold_minutes,
                    business_calendar_ref, start_event, completion_event,
                    approved_pause_reasons, lifecycle_status, effective_from,
                    effective_to, created_by_ref, correlation_id,
                    idempotency_key_hash, request_payload_hash, metadata, redactions
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                    $14::jsonb, 'DRAFT', $15, $16, $17, $18, $19, $20, $21::jsonb, $22::jsonb
                ) RETURNING *
                """,
                policy_id, code, version_number, jurisdiction, safe_work_type, category,
                safe_priority, business_timezone, target_duration_minutes,
                warning_threshold_minutes, business_calendar_ref, safe_start_event,
                safe_completion_event, json.dumps(list(pause_reasons)), start, end,
                actor_ref, correlation_id, idempotency_key_hash, request_payload_hash,
                json.dumps(dict(metadata)), json.dumps(list(POLICY_REDACTIONS)),
            )
            await _audit(
                conn, policy_id=str(policy_id), event_type="POLICY_CREATED", event_status="SUCCESS",
                actor_ref=actor_ref, actor_role=actor_role, reason_code="NEW_POLICY_VERSION",
                correlation_id=correlation_id, idempotency_key_hash=idempotency_key_hash,
                request_payload_hash=request_payload_hash,
                evidence_summary={"policyCode": code, "versionNumber": version_number, "nextStatus": "DRAFT"},
            )
            return _policy_from_row(row), "NEW_REQUEST"


async def list_service_target_policies(
    *, lifecycle_status: str | None = None, operating_jurisdiction_code: str | None = None,
    work_type: str | None = None, work_category: str | None = None, priority: str | None = None,
) -> list[ServiceTargetPolicy]:
    status = lifecycle_status.upper() if lifecycle_status else None
    if status and status not in POLICY_LIFECYCLE_STATUSES:
        raise ServiceTargetPolicyValidationError("lifecycleStatus is invalid.")
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM referral_saas_operational_service_target_policies
            WHERE ($1::text IS NULL OR lifecycle_status = $1)
              AND ($2::text IS NULL OR operating_jurisdiction_code = $2)
              AND ($3::text IS NULL OR work_type = $3)
              AND ($4::text IS NULL OR work_category = $4)
              AND ($5::text IS NULL OR priority = $5)
            ORDER BY policy_code, version_number DESC
            """,
            status,
            _normalise_code(operating_jurisdiction_code, "operatingJurisdictionCode") if operating_jurisdiction_code else None,
            _normalise_code(work_type, "workType") if work_type else None,
            _normalise_code(work_category, "workCategory") if work_category else None,
            _normalise_code(priority, "priority") if priority else None,
        )
    return [_policy_from_row(row) for row in rows]


async def _load_policy_for_update(conn: Any, policy_ref: str) -> Mapping[str, Any]:
    try:
        policy_id = uuid.UUID(policy_ref)
    except ValueError as exc:
        raise ServiceTargetPolicyValidationError("policyRef must be a UUID.") from exc
    row = await conn.fetchrow(
        "SELECT * FROM referral_saas_operational_service_target_policies WHERE service_target_policy_id = $1 FOR UPDATE",
        policy_id,
    )
    if not row:
        raise ServiceTargetPolicyNotFound(policy_ref)
    return row


async def transition_service_target_policy(
    *, policy_ref: str, action: str, reason: str, actor_ref: str, actor_role: str,
    correlation_id: str, idempotency_key_hash: str, request_payload_hash: str,
) -> tuple[ServiceTargetPolicy, str]:
    safe_action = _normalise_code(action, "action")
    if safe_action not in {"SUBMIT_REVIEW", "APPROVE", "RETURN_TO_DRAFT", "RETIRE"}:
        raise ServiceTargetPolicyValidationError("Unsupported policy lifecycle action.")
    if not str(reason or "").strip():
        raise ServiceTargetPolicyValidationError("reason is required.")
    transitions = {
        "SUBMIT_REVIEW": ("DRAFT", "IN_REVIEW"),
        "APPROVE": ("IN_REVIEW", "APPROVED"),
        "RETURN_TO_DRAFT": ("IN_REVIEW", "DRAFT"),
        "RETIRE": ("APPROVED", "RETIRED"),
    }
    expected, next_status = transitions[safe_action]
    async with db_connection() as conn:
        async with conn.transaction():
            policy = await _load_policy_for_update(conn, policy_ref)
            replay = await conn.fetchrow(
                """SELECT request_payload_hash FROM referral_saas_operational_service_target_audit
                   WHERE entity_type = 'POLICY' AND entity_ref = $1 AND idempotency_key_hash = $2
                   ORDER BY created_at DESC LIMIT 1""",
                uuid.UUID(policy_ref), idempotency_key_hash,
            )
            if replay:
                if _row_value(replay, "request_payload_hash") != request_payload_hash:
                    raise ServiceTargetPolicyConflict("Idempotency key was reused with different lifecycle content.")
                return _policy_from_row(policy), "REPLAY_SAME_PAYLOAD"
            current = str(_row_value(policy, "lifecycle_status"))
            if current != expected:
                raise ServiceTargetPolicyConflict(f"{safe_action} requires {expected}; current status is {current}.")
            if safe_action in {"APPROVE", "RETURN_TO_DRAFT"} and actor_ref == str(_row_value(policy, "created_by_ref")):
                raise ServiceTargetPolicyConflict("Policy review must be performed by an actor other than the creator.")
            if safe_action == "APPROVE":
                overlap = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM referral_saas_operational_service_target_policies
                        WHERE service_target_policy_id <> $1
                          AND lifecycle_status = 'APPROVED'
                          AND operating_jurisdiction_code = $2 AND work_type = $3
                          AND work_category = $4 AND priority = $5
                          AND effective_from < COALESCE($7, 'infinity'::timestamptz)
                          AND COALESCE(effective_to, 'infinity'::timestamptz) > $6
                    )
                    """,
                    uuid.UUID(policy_ref), _row_value(policy, "operating_jurisdiction_code"),
                    _row_value(policy, "work_type"), _row_value(policy, "work_category"),
                    _row_value(policy, "priority"), _row_value(policy, "effective_from"),
                    _row_value(policy, "effective_to"),
                )
                if overlap:
                    raise ServiceTargetPolicyConflict("An approved policy already covers this effective dimension window.")
            row = await conn.fetchrow(
                """
                UPDATE referral_saas_operational_service_target_policies
                SET lifecycle_status = $2,
                    reviewed_by_ref = CASE WHEN $3 IN ('APPROVE', 'RETURN_TO_DRAFT') THEN $4 ELSE reviewed_by_ref END,
                    reviewed_at = CASE WHEN $3 IN ('APPROVE', 'RETURN_TO_DRAFT') THEN NOW() ELSE reviewed_at END,
                    approved_by_ref = CASE WHEN $3 = 'APPROVE' THEN $4 ELSE approved_by_ref END,
                    approved_at = CASE WHEN $3 = 'APPROVE' THEN NOW() ELSE approved_at END,
                    retired_at = CASE WHEN $3 = 'RETIRE' THEN NOW() ELSE retired_at END,
                    updated_at = NOW()
                WHERE service_target_policy_id = $1 RETURNING *
                """,
                uuid.UUID(policy_ref), next_status, safe_action, actor_ref,
            )
            await _audit(
                conn, policy_id=policy_ref, event_type=f"POLICY_{safe_action}", event_status="SUCCESS",
                actor_ref=actor_ref, actor_role=actor_role, reason_code=str(reason).strip(),
                correlation_id=correlation_id, idempotency_key_hash=idempotency_key_hash,
                request_payload_hash=request_payload_hash,
                evidence_summary={"previousStatus": current, "nextStatus": next_status},
            )
            return _policy_from_row(row), "NEW_REQUEST"


async def resolve_service_target_policy(
    *, operating_jurisdiction_code: str, work_type: str, work_category: str,
    priority: str, effective_at: datetime | None = None,
) -> ServiceTargetPolicy:
    at = _normalise_datetime(effective_at, "effectiveAt") if effective_at else datetime.now(timezone.utc)
    dimensions = (
        _normalise_code(operating_jurisdiction_code, "operatingJurisdictionCode"),
        _normalise_code(work_type, "workType"),
        _normalise_code(work_category, "workCategory"),
        _normalise_code(priority, "priority"),
    )
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM referral_saas_operational_service_target_policies
            WHERE operating_jurisdiction_code = $1 AND work_type = $2
              AND work_category = $3 AND priority = $4
              AND lifecycle_status = 'APPROVED'
              AND effective_from <= $5 AND (effective_to IS NULL OR effective_to > $5)
            ORDER BY effective_from DESC, version_number DESC LIMIT 2
            """,
            *dimensions, at,
        )
    if not rows:
        raise ServiceTargetPolicyResolutionUnavailable("No approved effective service-target policy covers these dimensions.")
    if len(rows) > 1:
        raise ServiceTargetPolicyResolutionUnavailable("Multiple approved service-target policies cover these dimensions.")
    return _policy_from_row(rows[0])
