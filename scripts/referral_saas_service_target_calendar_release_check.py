from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.referral_saas_operational_service_clock_service import (
    apply_support_case_status_to_service_target_clock,
    change_service_target_pause_state,
    start_support_case_service_target_clock,
)
from services.referral_saas_operational_service_target_service import (
    create_service_target_policy,
    transition_service_target_policy,
)
from services.referral_saas_service_target_calendar_service import (
    DateException,
    ServiceTargetCalendarConflict,
    WeeklyInterval,
    create_service_target_calendar,
    preview_service_target_calendar,
    resolve_service_target_calendar,
    transition_service_target_calendar,
)
from utils import db


RUN_PREFIX = "TASK443_RELEASE_PROOF"
JURISDICTIONS = ("ZA", "BW")
CALENDAR_CODE = "TASK443_SUPPORT"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _key(run_ref: str, action: str) -> str:
    return _hash(f"{RUN_PREFIX}:{run_ref}:{action}")


def cleanup_statements() -> tuple[str, ...]:
    return (
        "DELETE FROM referral_saas_operational_service_target_audit WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_operational_service_target_pause_events WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_operational_service_target_clocks WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_support_cases WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_operational_service_target_policies WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_service_target_calendar_audit WHERE correlation_id LIKE $1",
        "DELETE FROM referral_saas_service_target_calendar_date_exceptions WHERE service_target_calendar_version_id IN (SELECT service_target_calendar_version_id FROM referral_saas_service_target_calendar_versions WHERE calendar_code = $1)",
        "DELETE FROM referral_saas_service_target_calendar_weekly_intervals WHERE service_target_calendar_version_id IN (SELECT service_target_calendar_version_id FROM referral_saas_service_target_calendar_versions WHERE calendar_code = $1)",
        "DELETE FROM referral_saas_service_target_calendar_versions WHERE calendar_code = $1",
        "DELETE FROM platform_accounts WHERE account_code LIKE $1",
        "DELETE FROM tenants WHERE tenant_code LIKE $1",
    )


async def _cleanup(conn: asyncpg.Connection, run_ref: str) -> None:
    values = (
        f"{RUN_PREFIX}:{run_ref}%", f"{RUN_PREFIX}:{run_ref}%",
        f"{RUN_PREFIX}:{run_ref}%", f"{RUN_PREFIX}:{run_ref}%",
        f"{RUN_PREFIX}:{run_ref}%", f"{RUN_PREFIX}:{run_ref}%",
        f"{CALENDAR_CODE}_{run_ref}", f"{CALENDAR_CODE}_{run_ref}",
        f"{CALENDAR_CODE}_{run_ref}", f"T443_{run_ref}%", f"T443_{run_ref}%",
    )
    async with conn.transaction():
        for statement, value in zip(cleanup_statements(), values, strict=True):
            await conn.execute(statement, value)


async def _fixture(conn: asyncpg.Connection, run_ref: str, jurisdiction: str) -> tuple[str, str]:
    tenant_code = f"T443_{run_ref}_{jurisdiction}"
    account_id, case_id = uuid.uuid4(), uuid.uuid4()
    await conn.execute(
        "INSERT INTO tenants (tenant_code, tenant_name, industry) VALUES ($1,$2,'test')",
        tenant_code, f"TASK-443 {jurisdiction}",
    )
    await conn.execute(
        """INSERT INTO platform_accounts (
               account_id, account_code, account_name, legal_organisation_name,
               trading_name, registration_number, account_type, status,
               onboarding_status, operating_jurisdiction_code, created_by_ref, updated_by_ref
           ) VALUES ($1,$2,$3,$3,$3,$4,'ORGANISATION','ACTIVE','APPROVED',$5,$6,$6)""",
        account_id, f"T443_{run_ref}_{jurisdiction}", f"TASK-443 {jurisdiction}",
        f"T443-{run_ref}-{jurisdiction}", jurisdiction, RUN_PREFIX,
    )
    await conn.execute(
        """INSERT INTO referral_saas_support_cases (
               support_case_id, account_id, tenant_code, category, priority, status,
               title, summary, source_surface, correlation_id, idempotency_key_hash,
               request_payload_hash, created_by_ref, created_by_role, updated_by_ref
           ) VALUES ($1,$2,$3,'MANUAL_REVIEW_REQUIRED','HIGH','OPEN',$4,$5,
                     'TASK_443_RELEASE_PROOF',$6,$7,$8,$9,'AMPLIFI_ADMIN',$9)""",
        case_id, account_id, tenant_code, f"TASK-443 {jurisdiction}",
        "Temporary PostgreSQL calendar proof.",
        f"{RUN_PREFIX}:{run_ref}:CASE:{jurisdiction}",
        _key(run_ref, f"case:{jurisdiction}"), _key(run_ref, f"case-payload:{jurisdiction}"),
        RUN_PREFIX,
    )
    return str(account_id), str(case_id)


async def _calendar(
    *, run_ref: str, scope: str, account_id: str | None, timezone_name: str,
    effective_from: datetime, effective_to: datetime | None = None,
):
    code = f"{CALENDAR_CODE}_{run_ref}"
    intervals = tuple(WeeklyInterval(day, time(8), time(17)) for day in range(1, 6))
    exceptions = (
        DateException(date(2026, 12, 25), "CLOSED", None, None, "PUBLIC_HOLIDAY"),
        DateException(date(2026, 12, 26), "WORKING_INTERVAL", time(9), time(12), "EXCEPTIONAL_HOURS"),
    )
    suffix = f"{scope}:{account_id or 'GLOBAL'}:{effective_from.isoformat()}"
    calendar, result = await create_service_target_calendar(
        calendar_code=code, scope_type=scope, account_id=account_id,
        calendar_name=f"TASK-443 {scope} calendar", business_timezone=timezone_name,
        effective_from=effective_from, effective_to=effective_to,
        weekly_intervals=intervals, date_exceptions=exceptions,
        metadata={"releaseProof": "TASK-443"}, actor_ref="task-443-author",
        actor_role="AMPLIFI_ADMIN", correlation_id=f"{RUN_PREFIX}:{run_ref}:CALENDAR:{suffix}",
        idempotency_key_hash=_key(run_ref, f"calendar:{suffix}"),
        request_payload_hash=_key(run_ref, f"calendar-payload:{suffix}"),
    )
    assert result == "NEW_REQUEST"
    for action, actor in (("SUBMIT_REVIEW", "task-443-author"), ("APPROVE", "task-443-reviewer")):
        calendar, transition = await transition_service_target_calendar(
            calendar_ref=calendar.calendar_version_id, action=action,
            reason="TASK-443 PostgreSQL release proof", actor_ref=actor,
            actor_role="AMPLIFI_ADMIN", correlation_id=f"{RUN_PREFIX}:{run_ref}:CALENDAR:{suffix}",
            idempotency_key_hash=_key(run_ref, f"calendar:{action}:{suffix}"),
            request_payload_hash=_key(run_ref, f"calendar:{action}:payload:{suffix}"),
        )
        assert transition == "NEW_REQUEST"
    return calendar


async def _policy(run_ref: str, now: datetime, calendar_code: str) -> None:
    policy, result = await create_service_target_policy(
        policy_code=f"T443_{run_ref}", operating_jurisdiction_code="ZA",
        work_type="SUPPORT_CASE", work_category="TASK443_CALENDAR_PROOF", priority="HIGH",
        business_timezone="Europe/London", target_duration_minutes=120,
        warning_threshold_minutes=60, start_event="SUPPORT_CASE_CREATED",
        completion_event="SUPPORT_CASE_RESOLVED", effective_from=now - timedelta(days=1),
        effective_to=now + timedelta(days=1), approved_pause_reasons=["CUSTOMER_RESPONSE_PENDING"],
        business_calendar_ref=calendar_code, metadata={"releaseProof": "TASK-443"},
        actor_ref="task-443-author", actor_role="AMPLIFI_ADMIN",
        correlation_id=f"{RUN_PREFIX}:{run_ref}:POLICY",
        idempotency_key_hash=_key(run_ref, "policy"), request_payload_hash=_key(run_ref, "policy-payload"),
    )
    assert result == "NEW_REQUEST"
    for action, actor in (("SUBMIT_REVIEW", "task-443-author"), ("APPROVE", "task-443-reviewer")):
        policy, result = await transition_service_target_policy(
            policy_ref=policy.policy_id, action=action, reason="TASK-443 release proof",
            actor_ref=actor, actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:POLICY",
            idempotency_key_hash=_key(run_ref, f"policy:{action}"),
            request_payload_hash=_key(run_ref, f"policy:{action}:payload"),
        )
        assert result == "NEW_REQUEST"


async def run_release_check(dsn: str) -> dict[str, object]:
    run_ref = uuid.uuid4().hex[:10].upper()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    code = f"{CALENDAR_CODE}_{run_ref}"
    db.APP_DB_DSN = dsn
    conn = await asyncpg.connect(dsn)
    try:
        await _cleanup(conn, run_ref)
        za_account, za_case = await _fixture(conn, run_ref, "ZA")
        fallback_account, _ = await _fixture(conn, run_ref, "BW")
        global_calendar = await _calendar(
            run_ref=run_ref, scope="GLOBAL", account_id=None,
            timezone_name="Europe/London", effective_from=now - timedelta(days=2),
        )
        account_calendar = await _calendar(
            run_ref=run_ref, scope="ACCOUNT", account_id=za_account,
            timezone_name="Europe/London", effective_from=now - timedelta(days=1),
        )
        assert (await resolve_service_target_calendar(calendar_code=code, account_id=za_account)).calendar_version_id == account_calendar.calendar_version_id
        assert (await resolve_service_target_calendar(calendar_code=code, account_id=fallback_account)).calendar_version_id == global_calendar.calendar_version_id

        overlap, _ = await create_service_target_calendar(
            calendar_code=code, scope_type="ACCOUNT", account_id=za_account,
            calendar_name="TASK-443 overlap", business_timezone="Europe/London",
            effective_from=now - timedelta(hours=1), effective_to=None,
            weekly_intervals=(WeeklyInterval(1, time(8), time(17)),), date_exceptions=(),
            metadata={}, actor_ref="task-443-author", actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:OVERLAP",
            idempotency_key_hash=_key(run_ref, "overlap"),
            request_payload_hash=_key(run_ref, "overlap-payload"),
        )
        await transition_service_target_calendar(
            calendar_ref=overlap.calendar_version_id, action="SUBMIT_REVIEW", reason="proof",
            actor_ref="task-443-author", actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:OVERLAP",
            idempotency_key_hash=_key(run_ref, "overlap-submit"),
            request_payload_hash=_key(run_ref, "overlap-submit-payload"),
        )
        try:
            await transition_service_target_calendar(
                calendar_ref=overlap.calendar_version_id, action="APPROVE", reason="proof",
                actor_ref="task-443-reviewer", actor_role="AMPLIFI_ADMIN",
                correlation_id=f"{RUN_PREFIX}:{run_ref}:OVERLAP",
                idempotency_key_hash=_key(run_ref, "overlap-approve"),
                request_payload_hash=_key(run_ref, "overlap-approve-payload"),
            )
            raise AssertionError("Overlapping calendar approval was not rejected.")
        except ServiceTargetCalendarConflict:
            pass

        closure = await preview_service_target_calendar(
            calendar_ref=account_calendar.calendar_version_id,
            started_at=datetime(2026, 12, 24, 16, 0, tzinfo=timezone.utc),
            warning_threshold_minutes=60, target_duration_minutes=180,
        )
        assert closure["dueAt"] > datetime(2026, 12, 26, 9, 0, tzinfo=timezone.utc)
        dst = await preview_service_target_calendar(
            calendar_ref=account_calendar.calendar_version_id,
            started_at=datetime(2026, 3, 27, 16, 0, tzinfo=timezone.utc),
            warning_threshold_minutes=60, target_duration_minutes=180,
        )
        assert dst["dueAt"].utcoffset() == timedelta(0)

        await _policy(run_ref, now, code)
        clock, started = await start_support_case_service_target_clock(
            account_id=za_account, support_case_id=za_case,
            operating_jurisdiction_code="ZA", work_category="TASK443_CALENDAR_PROOF",
            priority="HIGH", started_at=now, actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:CLOCK",
            idempotency_key_hash=_key(run_ref, "clock"), request_payload_hash=_key(run_ref, "clock-payload"),
        )
        assert clock and started == "CLOCK_STARTED"
        assert clock.calendar_version_id == account_calendar.calendar_version_id
        replay, replay_result = await start_support_case_service_target_clock(
            account_id=za_account, support_case_id=za_case,
            operating_jurisdiction_code="ZA", work_category="TASK443_CALENDAR_PROOF",
            priority="HIGH", started_at=now, actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:CLOCK",
            idempotency_key_hash=_key(run_ref, "clock"), request_payload_hash=_key(run_ref, "clock-payload"),
        )
        assert replay and replay.clock_id == clock.clock_id and replay_result == "CLOCK_REPLAYED"
        paused, pause_result = await change_service_target_pause_state(
            account_id=za_account, support_case_id=za_case, action="PAUSE",
            pause_reason_code="CUSTOMER_RESPONSE_PENDING", event_at=now + timedelta(minutes=10),
            actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN", correlation_id=f"{RUN_PREFIX}:{run_ref}:PAUSE",
            idempotency_key_hash=_key(run_ref, "pause"), request_payload_hash=_key(run_ref, "pause-payload"),
        )
        resumed, resume_result = await change_service_target_pause_state(
            account_id=za_account, support_case_id=za_case, action="RESUME",
            pause_reason_code="CUSTOMER_RESPONSE_PENDING", event_at=now + timedelta(minutes=20),
            actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN", correlation_id=f"{RUN_PREFIX}:{run_ref}:RESUME",
            idempotency_key_hash=_key(run_ref, "resume"), request_payload_hash=_key(run_ref, "resume-payload"),
        )
        assert paused.clock_status == "PAUSED" and pause_result == "CLOCK_PAUSED"
        assert resumed.calendar_version_id == account_calendar.calendar_version_id and resume_result == "CLOCK_RESUMED"
        completed, completion = await apply_support_case_status_to_service_target_clock(
            account_id=za_account, support_case_id=za_case, from_status="OPEN", to_status="RESOLVED",
            changed_at=now + timedelta(minutes=30), actor_ref=RUN_PREFIX, actor_role="AMPLIFI_ADMIN",
            correlation_id=f"{RUN_PREFIX}:{run_ref}:COMPLETE",
            idempotency_key_hash=_key(run_ref, "complete"), request_payload_hash=_key(run_ref, "complete-payload"),
        )
        assert completed and completion == "CLOCK_COMPLETED"
        audit_count = await conn.fetchval(
            "SELECT COUNT(*) FROM referral_saas_service_target_calendar_audit WHERE correlation_id LIKE $1",
            f"{RUN_PREFIX}:{run_ref}%",
        )
        redaction_count = await conn.fetchval(
            "SELECT COUNT(*) FROM referral_saas_service_target_calendar_audit WHERE correlation_id LIKE $1 AND jsonb_array_length(redactions) > 0",
            f"{RUN_PREFIX}:{run_ref}%",
        )
        assert audit_count >= 7 and redaction_count == audit_count
        return {
            "status": "PASS", "runRef": run_ref, "jurisdictions": list(JURISDICTIONS),
            "accountOverride": True, "globalFallback": True, "overlapRejected": True,
            "closureAndExceptionalHours": True, "dstTimezone": "Europe/London",
            "calendarVersionPinned": True, "pauseResumeCompletion": True,
            "auditRecords": audit_count, "redactionsVerified": True,
        }
    finally:
        await db.close_async_pool()
        await _cleanup(conn, run_ref)
        remaining = await conn.fetchval(
            "SELECT COUNT(*) FROM referral_saas_service_target_calendar_versions WHERE calendar_code=$1", code,
        )
        await conn.close()
        if remaining:
            raise RuntimeError("TASK-443 temporary calendar evidence was not removed.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify governed business calendars against PostgreSQL.")
    parser.add_argument("--db-dsn", default=os.environ.get("APP_DB_DSN"))
    args = parser.parse_args()
    if not args.db_dsn:
        parser.error("--db-dsn or APP_DB_DSN is required")
    print(json.dumps(asyncio.run(run_release_check(args.db_dsn)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
