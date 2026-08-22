"""Server-owned operational service-target clocks for Referral SaaS support work."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
from typing import Any, Mapping
import uuid

from services.referral_saas_operational_service_target_service import (
    ServiceTargetPolicyResolutionUnavailable,
    resolve_service_target_policy,
)
from utils.db import db_connection


CLOCK_GUARDRAILS = (
    "SERVER_OWNED_CLOCK",
    "APPROVED_POLICY_VERSION_PINNED",
    "APPROVED_PAUSE_REASON_REQUIRED",
    "NO_BROWSER_TIMER",
    "NO_BILLING_OR_MONEY_MOVEMENT",
)
CLOCK_REDACTIONS = ("idempotency_key_hash", "request_payload_hash", "tenant_code")


class ServiceTargetClockError(Exception):
    pass


class ServiceTargetClockValidationError(ServiceTargetClockError):
    pass


class ServiceTargetClockConflict(ServiceTargetClockError):
    pass


class ServiceTargetClockNotFound(ServiceTargetClockError):
    pass


@dataclass(frozen=True)
class ServiceTargetClock:
    clock_id: str
    support_case_id: str
    account_id: str
    policy_id: str
    policy_code: str
    policy_version_number: int
    clock_status: str
    started_at: datetime
    warning_at: datetime
    due_at: datetime
    accumulated_paused_seconds: int
    completed_at: datetime | None
    breached_at: datetime | None
    completion_outcome: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _value(row: Mapping[str, Any], key: str, default: Any = None) -> Any:
    try:
        return row[key]
    except (KeyError, TypeError):
        return default


def _clock(row: Mapping[str, Any]) -> ServiceTargetClock:
    return ServiceTargetClock(
        clock_id=str(_value(row, "service_target_clock_id")),
        support_case_id=str(_value(row, "support_case_id")),
        account_id=str(_value(row, "account_id")),
        policy_id=str(_value(row, "service_target_policy_id")),
        policy_code=str(_value(row, "policy_code")),
        policy_version_number=int(_value(row, "policy_version_number")),
        clock_status=str(_value(row, "clock_status")),
        started_at=_value(row, "started_at"),
        warning_at=_value(row, "warning_at"),
        due_at=_value(row, "due_at"),
        accumulated_paused_seconds=int(_value(row, "accumulated_paused_seconds", 0)),
        completed_at=_value(row, "completed_at"),
        breached_at=_value(row, "breached_at"),
        completion_outcome=_value(row, "completion_outcome"),
    )


def _json_object(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, Mapping):
        raise ServiceTargetClockValidationError("Clock metadata must be an object.")
    return dict(value)


def _clock_window(
    *, started_at: datetime, warning_threshold_minutes: int,
    target_duration_minutes: int,
) -> tuple[datetime, datetime, datetime]:
    start = started_at.astimezone(timezone.utc)
    return (
        start,
        start + timedelta(minutes=warning_threshold_minutes),
        start + timedelta(minutes=target_duration_minutes),
    )


async def _audit(
    conn: Any, *, clock_id: str, account_id: str, event_type: str,
    actor_ref: str, actor_role: str, reason_code: str, correlation_id: str,
    idempotency_key_hash: str, request_payload_hash: str,
    evidence: Mapping[str, Any],
) -> None:
    await conn.execute(
        """
        INSERT INTO referral_saas_operational_service_target_audit (
            service_target_audit_id, entity_type, entity_ref, account_id,
            event_type, event_status, actor_ref, actor_role, reason_code,
            correlation_id, idempotency_key_hash, request_payload_hash,
            evidence_summary, redactions
        ) VALUES ($1, 'CLOCK', $2, $3, $4, 'SUCCESS', $5, $6, $7,
                  $8, $9, $10, $11::jsonb, $12::jsonb)
        """,
        uuid.uuid4(), uuid.UUID(clock_id), uuid.UUID(account_id), event_type,
        actor_ref, actor_role, reason_code, correlation_id,
        idempotency_key_hash, request_payload_hash, json.dumps(dict(evidence)),
        json.dumps(list(CLOCK_REDACTIONS)),
    )


async def start_support_case_service_target_clock(
    *, account_id: str, support_case_id: str, operating_jurisdiction_code: str,
    work_category: str, priority: str, started_at: datetime,
    actor_ref: str, actor_role: str, correlation_id: str,
    idempotency_key_hash: str, request_payload_hash: str,
) -> tuple[ServiceTargetClock | None, str]:
    """Start a clock when one approved policy covers the support case."""
    try:
        policy = await resolve_service_target_policy(
            operating_jurisdiction_code=operating_jurisdiction_code,
            work_type="SUPPORT_CASE", work_category=work_category,
            priority=priority, effective_at=started_at,
        )
    except ServiceTargetPolicyResolutionUnavailable:
        return None, "POLICY_UNAVAILABLE"
    if policy.start_event != "SUPPORT_CASE_CREATED":
        return None, "START_EVENT_UNAVAILABLE"
    if policy.business_calendar_ref:
        return None, "BUSINESS_CALENDAR_UNAVAILABLE"
    start, warning_at, due_at = _clock_window(
        started_at=started_at,
        warning_threshold_minutes=policy.warning_threshold_minutes,
        target_duration_minutes=policy.target_duration_minutes,
    )
    async with db_connection() as conn:
        async with conn.transaction():
            existing = await conn.fetchrow(
                "SELECT * FROM referral_saas_operational_service_target_clocks WHERE support_case_id = $1",
                uuid.UUID(support_case_id),
            )
            if existing:
                return _clock(existing), "CLOCK_REPLAYED"
            clock_id = uuid.uuid4()
            row = await conn.fetchrow(
                """
                INSERT INTO referral_saas_operational_service_target_clocks (
                    service_target_clock_id, support_case_id, account_id,
                    service_target_policy_id, policy_code, policy_version_number,
                    clock_status, started_at, warning_at, due_at, correlation_id,
                    idempotency_key_hash, request_payload_hash, created_by_ref,
                    updated_by_ref, metadata, redactions
                ) VALUES ($1, $2, $3, $4, $5, $6, 'RUNNING', $7, $8, $9,
                          $10, $11, $12, $13, $13, $14::jsonb, $15::jsonb)
                RETURNING *
                """,
                clock_id, uuid.UUID(support_case_id), uuid.UUID(account_id),
                uuid.UUID(policy.policy_id), policy.policy_code,
                policy.version_number, start, warning_at, due_at, correlation_id,
                idempotency_key_hash, request_payload_hash, actor_ref,
                json.dumps({"businessTimezone": policy.business_timezone}),
                json.dumps(list(CLOCK_REDACTIONS)),
            )
            await _audit(
                conn, clock_id=str(clock_id), account_id=account_id,
                event_type="CLOCK_STARTED", actor_ref=actor_ref,
                actor_role=actor_role, reason_code="SUPPORT_CASE_CREATED",
                correlation_id=correlation_id,
                idempotency_key_hash=idempotency_key_hash,
                request_payload_hash=request_payload_hash,
                evidence={"policyCode": policy.policy_code,
                          "policyVersionNumber": policy.version_number,
                          "startedAt": start.isoformat(), "dueAt": due_at.isoformat()},
            )
            return _clock(row), "CLOCK_STARTED"


async def apply_support_case_status_to_service_target_clock(
    *, account_id: str, support_case_id: str, from_status: str, to_status: str,
    changed_at: datetime, actor_ref: str, actor_role: str,
    correlation_id: str, idempotency_key_hash: str, request_payload_hash: str,
) -> tuple[ServiceTargetClock | None, str]:
    terminal = {"RESOLVED", "CLOSED"}
    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """SELECT c.*, p.completion_event
                   FROM referral_saas_operational_service_target_clocks c
                   JOIN referral_saas_operational_service_target_policies p
                     ON p.service_target_policy_id = c.service_target_policy_id
                   WHERE c.account_id = $1 AND c.support_case_id = $2
                   FOR UPDATE OF c""",
                uuid.UUID(account_id), uuid.UUID(support_case_id),
            )
            if not row:
                return None, "CLOCK_UNAVAILABLE"
            current = _clock(row)
            event_at = changed_at.astimezone(timezone.utc)
            completion_status = {
                "SUPPORT_CASE_RESOLVED": "RESOLVED",
                "SUPPORT_CASE_CLOSED": "CLOSED",
            }.get(str(_value(row, "completion_event", "")).upper())
            if not completion_status:
                return current, "COMPLETION_EVENT_UNAVAILABLE"
            if to_status == completion_status and current.clock_status != "COMPLETED":
                outcome = "LATE" if event_at > current.due_at else "WITHIN_TARGET"
                updated = await conn.fetchrow(
                    """UPDATE referral_saas_operational_service_target_clocks
                       SET clock_status='COMPLETED', completed_at=$3,
                           breached_at=CASE WHEN $3 > due_at THEN COALESCE(breached_at, due_at) ELSE breached_at END,
                           completion_outcome=$4, updated_by_ref=$5, updated_at=NOW()
                       WHERE account_id=$1 AND support_case_id=$2 RETURNING *""",
                    uuid.UUID(account_id), uuid.UUID(support_case_id), event_at,
                    outcome, actor_ref,
                )
                event_type = "CLOCK_COMPLETED"
            elif from_status in terminal and to_status not in terminal and current.clock_status == "COMPLETED":
                await _audit(
                    conn, clock_id=current.clock_id, account_id=account_id,
                    event_type="CLOCK_PRIOR_OUTCOME_PRESERVED", actor_ref=actor_ref,
                    actor_role=actor_role, reason_code="SUPPORT_CASE_REOPENED",
                    correlation_id=correlation_id,
                    idempotency_key_hash=idempotency_key_hash + ":prior",
                    request_payload_hash=request_payload_hash,
                    evidence={"completedAt": current.completed_at.isoformat() if current.completed_at else None,
                              "completionOutcome": current.completion_outcome,
                              "breachedAt": current.breached_at.isoformat() if current.breached_at else None},
                )
                updated = await conn.fetchrow(
                    """UPDATE referral_saas_operational_service_target_clocks
                       SET clock_status='RUNNING', completed_at=NULL,
                           completion_outcome=NULL, updated_by_ref=$3, updated_at=NOW()
                       WHERE account_id=$1 AND support_case_id=$2 RETURNING *""",
                    uuid.UUID(account_id), uuid.UUID(support_case_id), actor_ref,
                )
                event_type = "CLOCK_REOPENED"
            else:
                return current, "CLOCK_UNCHANGED"
            await _audit(
                conn, clock_id=current.clock_id, account_id=account_id,
                event_type=event_type, actor_ref=actor_ref, actor_role=actor_role,
                reason_code="SUPPORT_CASE_STATUS_CHANGED",
                correlation_id=correlation_id,
                idempotency_key_hash=idempotency_key_hash,
                request_payload_hash=request_payload_hash,
                evidence={"fromStatus": from_status, "toStatus": to_status},
            )
            return _clock(updated), event_type


async def change_service_target_pause_state(
    *, account_id: str, support_case_id: str, action: str, pause_reason_code: str,
    event_at: datetime, actor_ref: str, actor_role: str, correlation_id: str,
    idempotency_key_hash: str, request_payload_hash: str,
) -> tuple[ServiceTargetClock, str]:
    action = action.strip().upper()
    if action not in {"PAUSE", "RESUME"}:
        raise ServiceTargetClockValidationError("action must be PAUSE or RESUME.")
    reason = pause_reason_code.strip().upper()
    async with db_connection() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """SELECT c.*, p.approved_pause_reasons
                   FROM referral_saas_operational_service_target_clocks c
                   JOIN referral_saas_operational_service_target_policies p
                     ON p.service_target_policy_id=c.service_target_policy_id
                   WHERE c.account_id=$1 AND c.support_case_id=$2 FOR UPDATE""",
                uuid.UUID(account_id), uuid.UUID(support_case_id),
            )
            if not row:
                raise ServiceTargetClockNotFound("Service-target clock was not found for this support case.")
            approved = _value(row, "approved_pause_reasons", [])
            if isinstance(approved, str):
                approved = json.loads(approved)
            if reason not in approved:
                raise ServiceTargetClockValidationError("pauseReasonCode is not approved by the resolved policy.")
            replay = await conn.fetchrow(
                "SELECT request_payload_hash FROM referral_saas_operational_service_target_pause_events WHERE service_target_clock_id=$1 AND idempotency_key_hash=$2",
                _value(row, "service_target_clock_id"), idempotency_key_hash,
            )
            if replay:
                if _value(replay, "request_payload_hash") != request_payload_hash:
                    raise ServiceTargetClockConflict("Idempotency key was reused with different pause content.")
                return _clock(row), "REPLAY_SAME_PAYLOAD"
            expected = "RUNNING" if action == "PAUSE" else "PAUSED"
            if str(_value(row, "clock_status")) != expected:
                raise ServiceTargetClockConflict(f"{action} requires clock status {expected}.")
            at = event_at.astimezone(timezone.utc)
            if action == "PAUSE" and at >= _value(row, "due_at"):
                raise ServiceTargetClockConflict(
                    "A service-target clock cannot be paused at or after its due time."
                )
            await conn.execute(
                """INSERT INTO referral_saas_operational_service_target_pause_events (
                    service_target_pause_event_id, service_target_clock_id,
                    support_case_id, account_id, event_type, pause_reason_code,
                    event_at, actor_ref, actor_role, correlation_id,
                    idempotency_key_hash, request_payload_hash, metadata, redactions
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,'{}'::jsonb,$13::jsonb)""",
                uuid.uuid4(), _value(row, "service_target_clock_id"),
                uuid.UUID(support_case_id), uuid.UUID(account_id),
                "PAUSED" if action == "PAUSE" else "RESUMED", reason, at,
                actor_ref, actor_role, correlation_id, idempotency_key_hash,
                request_payload_hash, json.dumps(list(CLOCK_REDACTIONS)),
            )
            if action == "PAUSE":
                metadata = _json_object(_value(row, "metadata"))
                metadata["pausedAt"] = at.isoformat()
                updated = await conn.fetchrow(
                    "UPDATE referral_saas_operational_service_target_clocks SET clock_status='PAUSED', metadata=$3::jsonb, updated_by_ref=$4, updated_at=NOW() WHERE account_id=$1 AND support_case_id=$2 RETURNING *",
                    uuid.UUID(account_id), uuid.UUID(support_case_id), json.dumps(metadata), actor_ref,
                )
            else:
                metadata = _json_object(_value(row, "metadata"))
                paused_at_value = metadata.pop("pausedAt", None)
                if not paused_at_value:
                    raise ServiceTargetClockConflict(
                        "Paused clock evidence is missing its server-owned pause time."
                    )
                paused_at = datetime.fromisoformat(str(paused_at_value))
                seconds = max(0, int((at - paused_at).total_seconds()))
                updated = await conn.fetchrow(
                    """UPDATE referral_saas_operational_service_target_clocks
                       SET clock_status='RUNNING', accumulated_paused_seconds=accumulated_paused_seconds+$3,
                           warning_at=warning_at+($3 * interval '1 second'),
                           due_at=due_at+($3 * interval '1 second'),
                           metadata=$4::jsonb, updated_by_ref=$5, updated_at=NOW()
                       WHERE account_id=$1 AND support_case_id=$2 RETURNING *""",
                    uuid.UUID(account_id), uuid.UUID(support_case_id), seconds,
                    json.dumps(metadata), actor_ref,
                )
            return _clock(updated), f"CLOCK_{action}D"
